import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.responses import success_response
from backend.app.database import get_db
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.loan_application import LoanApplication
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.manual_review import (
    ManualReviewCheckerDecision,
    ManualReviewCreate,
    ManualReviewRecommendation,
    ManualReviewResponse,
    ManualReviewStart,
)
from backend.app.services.audit_log_service import audit_log_service
from backend.app.services.manual_review_history_service import (
    manual_review_history_service,
)
from backend.app.services.manual_review_service import manual_review_service


router = APIRouter(
    prefix="/manual-review",
    tags=["Manual Credit Review"],
)


@router.post(
    "",
    response_model=ApiResponse[ManualReviewResponse],
)
def create_manual_review(
    review: ManualReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        result = manual_review_service.create_review(
            db=db,
            application_id=review.application_id,
            review_reason=review.review_reason,
        )

        manual_review_history_service.record(
            db=db,
            review_id=result.review_id,
            application_id=result.application_id,
            action="REVIEW_CREATED",
            previous_status=None,
            new_status="OPEN",
            actor_type="SYSTEM",
            remarks=result.review_reason,
        )

        db.commit()
        db.refresh(result)

        response_data = ManualReviewResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Manual review created successfully.",
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MANUAL_REVIEW_CREATION_FAILED",
        )


@router.get(
    "/{application_id}",
    response_model=ApiResponse[ManualReviewResponse],
)
def get_manual_review(
    application_id: str,
    request: Request,
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

    response_data = ManualReviewResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Manual review retrieved successfully.",
    )


@router.get(
    "/{application_id}/history",
    response_model=ApiResponse[Any],
)
def get_manual_review_history(
    application_id: str,
    request: Request,
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

    result = manual_review_history_service.get_by_review(
        db=db,
        review_id=review.review_id,
    )

    return success_response(
        request=request,
        data=result,
        message="Manual review history retrieved successfully.",
    )


@router.post(
    "/{application_id}/start",
    response_model=ApiResponse[ManualReviewResponse],
)
def start_manual_review(
    application_id: str,
    start_request: ManualReviewStart,
    request: Request,
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

    try:
        previous_status = review.review_status

        result = manual_review_service.start_review(
            db=db,
            review=review,
            reviewer_id=start_request.reviewer_id,
        )

        manual_review_history_service.record(
            db=db,
            review_id=result.review_id,
            application_id=result.application_id,
            action="REVIEW_STARTED",
            previous_status=previous_status,
            new_status=result.review_status,
            actor_type="USER",
            actor_reference=result.reviewer_id,
            reviewer_id=result.reviewer_id,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            actor_type="USER",
            actor_reference=result.reviewer_id,
            action="MANUAL_REVIEW_STARTED",
            entity_type="MANUAL_REVIEW",
            entity_reference=result.review_id,
            description="Manual credit review started.",
            previous_state=previous_status,
            new_state=result.review_status,
            request_reference=application_id,
        )

        db.commit()
        db.refresh(result)

        response_data = ManualReviewResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Manual review started successfully.",
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MANUAL_REVIEW_START_FAILED",
        )


@router.post(
    "/{application_id}/recommendation",
    response_model=ApiResponse[ManualReviewResponse],
)
def submit_manual_review_recommendation(
    application_id: str,
    recommendation: ManualReviewRecommendation,
    request: Request,
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

    if review.review_status != "IN_PROGRESS":
        raise HTTPException(
            status_code=400,
            detail="Manual review must be IN_PROGRESS.",
        )

    try:
        previous_status = review.review_status

        result = manual_review_service.submit_recommendation(
            db=db,
            review=review,
            reviewer_id=recommendation.reviewer_id,
            reviewer_decision=recommendation.reviewer_decision,
            reviewer_remarks=recommendation.reviewer_remarks,
        )

        manual_review_history_service.record(
            db=db,
            review_id=result.review_id,
            application_id=result.application_id,
            action="REVIEW_RECOMMENDATION",
            previous_status=previous_status,
            new_status=result.review_status,
            actor_type="USER",
            actor_reference=recommendation.reviewer_id,
            reviewer_id=recommendation.reviewer_id,
            reviewer_decision=recommendation.reviewer_decision,
            remarks=recommendation.reviewer_remarks,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            actor_type="USER",
            actor_reference=recommendation.reviewer_id,
            action="MANUAL_REVIEW_RECOMMENDATION",
            entity_type="MANUAL_REVIEW",
            entity_reference=result.review_id,
            description=(
                f"Manual reviewer submitted recommendation "
                f"{recommendation.reviewer_decision}."
            ),
            previous_state=previous_status,
            new_state=result.review_status,
            request_reference=application_id,
        )

        db.commit()
        db.refresh(result)

        response_data = ManualReviewResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Manual review recommendation submitted successfully.",
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MANUAL_REVIEW_RECOMMENDATION_FAILED",
        )


@router.post(
    "/{application_id}/checker-decision",
    response_model=ApiResponse[ManualReviewResponse],
)
def submit_manual_review_checker_decision(
    application_id: str,
    decision: ManualReviewCheckerDecision,
    request: Request,
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

    if review.review_status != "PENDING_CHECKER":
        raise HTTPException(
            status_code=400,
            detail="Manual review must be PENDING_CHECKER.",
        )

    if review.reviewer_id == decision.checker_id.strip():
        raise HTTPException(
            status_code=403,
            detail="MAKER_CANNOT_BE_CHECKER",
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

    if credit_decision.decision != "REFER":
        raise HTTPException(
            status_code=409,
            detail="MANUAL_REVIEW_CREDIT_DECISION_NOT_REFER",
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

    if application_record.status not in {
        "SUBMITTED",
        "UNDERWRITING_COMPLETED",
        "REFERRED",
    }:
        raise HTTPException(
            status_code=409,
            detail="APPLICATION_NOT_ELIGIBLE_FOR_MANUAL_REVIEW_DECISION",
        )

    try:
        previous_status = review.review_status

        result = manual_review_service.submit_checker_decision(
            db=db,
            review=review,
            checker_id=decision.checker_id,
            checker_decision=decision.checker_decision,
            checker_remarks=decision.checker_remarks,
        )

        credit_decision.decision = decision.checker_decision

        application_record.status = {
            "APPROVE": "APPROVED",
            "REJECT": "REJECTED",
        }[decision.checker_decision]

        manual_review_history_service.record(
            db=db,
            review_id=result.review_id,
            application_id=result.application_id,
            action="CHECKER_DECISION",
            previous_status=previous_status,
            new_status=result.review_status,
            actor_type="USER",
            actor_reference=decision.checker_id,
            reviewer_id=result.reviewer_id,
            reviewer_decision=result.reviewer_decision,
            remarks=decision.checker_remarks,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            actor_type="USER",
            actor_reference=decision.checker_id,
            action="MANUAL_REVIEW_CHECKER_DECISION",
            entity_type="MANUAL_REVIEW",
            entity_reference=result.review_id,
            description=(
                f"Checker finalized manual credit review with decision "
                f"{decision.checker_decision}."
            ),
            previous_state="PENDING_CHECKER",
            new_state="COMPLETED",
            request_reference=application_id,
        )

        db.commit()
        db.refresh(result)

        response_data = ManualReviewResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Manual review checker decision completed successfully.",
        )

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MANUAL_REVIEW_CHECKER_DECISION_FAILED",
        )