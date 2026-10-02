import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.manual_review import ManualReview
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.loan_application import LoanApplication

from backend.app.schemas.manual_review import (
    ManualReviewCreate,
    ManualReviewResponse,
    ManualReviewDecision,
)
from backend.app.services.manual_review_service import manual_review_service
from backend.app.services.audit_log_service import audit_log_service


router = APIRouter(
    prefix="/manual-review",
    tags=["Manual Credit Review"],
)


@router.post(
    "",
    response_model=ManualReviewResponse,
)
def create_manual_review(
    review: ManualReviewCreate,
    db: Session = Depends(get_db),
):
    try:
        result = manual_review_service.create_review(
            db=db,
            application_id=review.application_id,
            review_reason=review.review_reason,
        )
        return result

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/{application_id}",
    response_model=ManualReviewResponse,
)
def get_manual_review(
    application_id: str,
    db: Session = Depends(get_db),
):
    result = manual_review_service.get_review(
        db=db,
        application_id=application_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Manual review not found.",
        )

    return result


@router.post(
    "/{application_id}/decision",
    response_model=ManualReviewResponse,
)
def submit_manual_review_decision(
    application_id: str,
    decision: ManualReviewDecision,
    db: Session = Depends(get_db),
):
    review = manual_review_service.get_review(
        db=db,
        application_id=application_id,
    )

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="Manual review not found.",
        )

    if review.review_status != "OPEN":
        raise HTTPException(
            status_code=400,
            detail="Manual review is already closed.",
        )

    if decision.reviewer_decision not in {"APPROVE", "REJECT"}:
        raise HTTPException(
            status_code=400,
            detail="Reviewer decision must be APPROVE or REJECT.",
        )

    credit_decision = (
        db.query(CreditDecision)
        .filter(
            CreditDecision.application_id == application_id,
        )
        .order_by(CreditDecision.created_at.desc())
        .first()
    )

    if credit_decision is None:
        raise HTTPException(
            status_code=404,
            detail="Credit decision not found.",
        )

    application_record = db.get(
        LoanApplication,
        application_id,
    )

    if application_record is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    review.reviewer_id = decision.reviewer_id
    review.reviewer_decision = decision.reviewer_decision
    review.reviewer_remarks = decision.reviewer_remarks
    review.review_status = "COMPLETED"

    credit_decision.decision = decision.reviewer_decision

    application_record.status = {
        "APPROVE": "APPROVED",
        "REJECT": "REJECTED",
    }[decision.reviewer_decision]

    audit_log_service.log(
        db=db,
        audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
        application_id=application_id,
        actor_type="USER",
        actor_reference=decision.reviewer_id,
        action="MANUAL_REVIEW_DECISION",
        entity_type="MANUAL_REVIEW",
        entity_reference=review.review_id,
        description=(
            f"Manual credit review completed with decision "
            f"{decision.reviewer_decision}"
        ),
        previous_state="OPEN",
        new_state="COMPLETED",
        request_reference=application_id,
    )

    db.commit()
    db.refresh(review)

    return review