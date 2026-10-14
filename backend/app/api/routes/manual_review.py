import uuid
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.responses import success_response
from backend.app.core.security import require_roles
from backend.app.core.request_context import get_request_id

from backend.app.database import get_db

from backend.app.models.auth_user import AuthUser
from backend.app.models.credit_decision import CreditDecision
from backend.app.models.loan_application import LoanApplication

from backend.app.schemas.common import ApiResponse
from backend.app.schemas.credit_decision import CreditDecisionOutput
from backend.app.schemas.manual_review import (
    ManualReviewCheckerDecision,
    ManualReviewCreate,
    ManualReviewRecommendation,
    ManualReviewResponse,
    ManualReviewStart,
    ManualReviewHistoryResponse,
)

from backend.app.services.audit_log_service import audit_log_service
from backend.app.services.credit_decision_service import (
    credit_decision_service,
)
from backend.app.services.decision_trace_service import (
    decision_trace_service,
)
from backend.app.services.manual_review_history_service import (
    manual_review_history_service,
)
from backend.app.services.manual_review_service import manual_review_service


router = APIRouter(
    prefix="/manual-review",
    tags=["Manual Credit Review"],
)

MANUAL_REVIEW_CREATE_ROLES = (
    "ADMIN",
    "CREDIT_ANALYST",
    "CREDIT_OFFICER",
    "RISK",
)

MANUAL_REVIEW_MAKER_ROLES = (
    "ADMIN",
    "CREDIT_ANALYST",
    "RISK",
)

MANUAL_REVIEW_CHECKER_ROLES = (
    "ADMIN",
    "CREDIT_OFFICER",
)

MANUAL_REVIEW_READ_ROLES = (
    "ADMIN",
    "CREDIT_ANALYST",
    "CREDIT_OFFICER",
    "RISK",
    "AUDITOR",
)

logger = logging.getLogger("backend.workflow")


def log_manual_review_event(
    level: int,
    event: str,
    request: Request,
    application_id: str,
    action: str,
    review_id: str | None = None,
    status: str | None = None,
    error_code: str | None = None,
) -> None:
    logger.log(
        level,
        "manual_review_%s request_id=%s application_id=%s "
        "action=%s review_id=%s status=%s error_code=%s",
        event,
        get_request_id(request),
        application_id,
        action,
        review_id or "-",
        status or "-",
        error_code or "-",
    )

def log_manual_review_precondition_failure(
    *,
    request: Request,
    application_id: str,
    action: str,
    error_code: str,
    review: Any | None = None,
) -> None:
    log_manual_review_event(
        level=logging.WARNING,
        event="failed",
        request=request,
        application_id=application_id,
        action=action,
        review_id=getattr(review, "review_id", None),
        status=getattr(review, "review_status", None),
        error_code=error_code,
    )

@router.post(
    "",
    response_model=ApiResponse[ManualReviewResponse],
)
def create_manual_review(
    review: ManualReviewCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(
        require_roles(*MANUAL_REVIEW_CREATE_ROLES),
    ),
):
    log_manual_review_event(
        logging.INFO,
        "started",
        request,
        review.application_id,
        "create",
    )

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
            actor_type="USER",
            remarks=result.review_reason,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.application_id,
            actor_type="USER",
            actor_reference=current_user.username,
            action="MANUAL_REVIEW_CREATED",
            entity_type="MANUAL_REVIEW",
            entity_reference=result.review_id,
            description="Manual review created by an authenticated user.",
            previous_state=None,
            new_state="OPEN",
            request_reference=result.application_id,
        )

        db.commit()
        db.refresh(result)
        
        log_manual_review_event(
            logging.INFO,
            "completed",
            request,
            result.application_id,
            "create",
            review_id=result.review_id,
            status=result.review_status,
        )

        response_data = ManualReviewResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Manual review created successfully.",
        )

    except ValueError as exc:
        db.rollback()
        
        log_manual_review_event(
            level=logging.WARNING,
            event="failed",
            request=request,
            application_id=review.application_id,
            action="create",
            error_code="MANUAL_REVIEW_CREATION_INVALID",
        )

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()

        log_manual_review_event(
            level=logging.ERROR,
            event="failed",
            request=request,
            application_id=review.application_id,
            action="create",
            error_code="MANUAL_REVIEW_CREATION_FAILED",
)
        
        logger.error(
            "manual_review_failed request_id=%s application_id=%s "
            "action=create error_type=unexpected",
            get_request_id(request),
            review.application_id,
        )
        raise HTTPException(
            status_code=500,
            detail="MANUAL_REVIEW_CREATION_FAILED",
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
    current_user: AuthUser = Depends(
        require_roles(*MANUAL_REVIEW_MAKER_ROLES),
    ),
):
    log_manual_review_event(
        level=logging.INFO,
        event="started",
        request=request,
        application_id=application_id,
        action="start",
    )
    
    review = manual_review_service.get_review(
        db=db,
        application_id=application_id,
    )

    if review is None:
        log_manual_review_precondition_failure(
            request=request,
            application_id=application_id,
            action="start",
            error_code="MANUAL_REVIEW_NOT_FOUND",
        )
        raise HTTPException(
            status_code=404,
            detail="Manual review not found.",
        )

    if start_request.reviewer_id != current_user.username:
        raise HTTPException(
            status_code=403,
            detail="REVIEWER_IDENTITY_MISMATCH",
        )

    log_manual_review_event(
        logging.INFO,
        "started",
        request,
        application_id,
        "start",
        review_id=review.review_id,
        status=review.review_status,
    )

    try:
        previous_status = review.review_status

        result = manual_review_service.start_review(
            db=db,
            review=review,
            reviewer_id=current_user.username,
        )

        manual_review_history_service.record(
            db=db,
            review_id=result.review_id,
            application_id=result.application_id,
            action="REVIEW_STARTED",
            previous_status=previous_status,
            new_status=result.review_status,
            actor_type="USER",
            actor_reference=current_user.username,
            reviewer_id=current_user.username,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            actor_type="USER",
            actor_reference=current_user.username,
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

        log_manual_review_event(
            logging.INFO,
            "completed",
            request,
            application_id,
            "start",
            review_id=result.review_id,
            status=result.review_status,
        )

        response_data = ManualReviewResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Manual review started successfully.",
        )

    except ValueError as exc:
        db.rollback()

        log_manual_review_event(
            logging.WARNING,
            "failed",
            request,
            application_id,
            "start",
            review_id=review.review_id,
            status=review.review_status,
            error_code=str(exc),
        )

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()

        log_manual_review_event(
            level=logging.ERROR,
            event="failed",
            request=request,
            application_id=application_id,
            action="start",
            review_id=review.review_id,
            status=review.review_status,
            error_code="MANUAL_REVIEW_START_FAILED",
        )

        logger.error(
            "manual_review_failed request_id=%s application_id=%s "
            "action=start error_type=unexpected",
            get_request_id(request),
            application_id,
        )

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
    current_user: AuthUser = Depends(
        require_roles(*MANUAL_REVIEW_MAKER_ROLES),
    ),
):
    review = manual_review_service.get_review(
        db=db,
        application_id=application_id,
    )

    if review is None:
        log_manual_review_precondition_failure(
            request=request,
            application_id=application_id,
            action="recommendation",
            error_code="MANUAL_REVIEW_NOT_FOUND",
        )
        raise HTTPException(
            status_code=404,
            detail="Manual review not found.",
        )

    if recommendation.reviewer_id != current_user.username:
        raise HTTPException(
            status_code=403,
            detail="REVIEWER_IDENTITY_MISMATCH",
        )

    if review.review_status != "IN_PROGRESS":
        log_manual_review_precondition_failure(
            request=request,
            application_id=application_id,
            action="recommendation",
            error_code="MANUAL_REVIEW_NOT_IN_PROGRESS",
            review=review,
        )
        raise HTTPException(
            status_code=400,
            detail="Manual review must be IN_PROGRESS.",
        )

    log_manual_review_event(
        logging.INFO,
        "started",
        request,
        application_id,
        "recommendation",
        review_id=review.review_id,
        status=review.review_status,
    )

    try:
        previous_status = review.review_status

        result = manual_review_service.submit_recommendation(
            db=db,
            review=review,
            reviewer_id=current_user.username,
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
            actor_reference=current_user.username,
            reviewer_id=current_user.username,
            reviewer_decision=recommendation.reviewer_decision,
            remarks=recommendation.reviewer_remarks,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            actor_type="USER",
            actor_reference=current_user.username,
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

        log_manual_review_event(
            logging.INFO,
            "completed",
            request,
            application_id,
            "recommendation",
            review_id=result.review_id,
            status=result.review_status,
        )

        response_data = ManualReviewResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Manual review recommendation submitted successfully.",
        )

    except ValueError as exc:
        db.rollback()

        log_manual_review_event(
            logging.WARNING,
            "failed",
            request,
            application_id,
            "recommendation",
            review_id=review.review_id,
            status=review.review_status,
            error_code=str(exc),
        )

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()

        log_manual_review_event(
            level=logging.ERROR,
            event="failed",
            request=request,
            application_id=application_id,
            action="recommendation",
            review_id=review.review_id,
            status=review.review_status,
            error_code="MANUAL_REVIEW_RECOMMENDATION_FAILED",
        )

        logger.error(
            "manual_review_failed request_id=%s application_id=%s "
            "action=recommendation error_type=unexpected",
            get_request_id(request),
            application_id,
        )

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
    current_user: AuthUser = Depends(
        require_roles(*MANUAL_REVIEW_CHECKER_ROLES),
    ),
):
    review = manual_review_service.get_review(
        db=db,
        application_id=application_id,
    )

    if review is None:
        log_manual_review_precondition_failure(
            request=request,
            application_id=application_id,
            action="checker_decision",
            error_code="MANUAL_REVIEW_NOT_FOUND",
        )
        raise HTTPException(
            status_code=404,
            detail="Manual review not found.",
        )

    if decision.checker_id.strip() != current_user.username:
        raise HTTPException(
            status_code=403,
            detail="CHECKER_IDENTITY_MISMATCH",
        )

    if review.review_status != "PENDING_CHECKER":
        log_manual_review_precondition_failure(
            request=request,
            application_id=application_id,
            action="checker_decision",
            error_code="MANUAL_REVIEW_NOT_PENDING_CHECKER",
            review=review,
        )
        raise HTTPException(
            status_code=400,
            detail="Manual review must be PENDING_CHECKER.",
        )

    if review.reviewer_id == current_user.username:
        log_manual_review_precondition_failure(
            request=request,
            application_id=application_id,
            action="checker_decision",
            error_code="MAKER_CANNOT_BE_CHECKER",
            review=review,
        )
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
        log_manual_review_precondition_failure(
            request=request,
            application_id=application_id,
            action="checker_decision",
            error_code="CREDIT_DECISION_NOT_FOUND",
            review=review,
        )
        raise HTTPException(
            status_code=404,
            detail="Credit decision not found.",
        )

    if credit_decision.decision != "REFER":
        log_manual_review_precondition_failure(
            request=request,
            application_id=application_id,
            action="checker_decision",
            error_code="CREDIT_DECISION_NOT_REFER",
            review=review,
        )
        raise HTTPException(
            status_code=409,
            detail="CREDIT_DECISION_NOT_REFER",
        )

    application_record = db.get(
        LoanApplication,
        application_id,
    )

    if application_record is None:
        log_manual_review_precondition_failure(
            request=request,
            application_id=application_id,
            action="checker_decision",
            error_code="APPLICATION_NOT_FOUND",
            review=review,
        )
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

    log_manual_review_event(
        logging.INFO,
        "started",
        request,
        application_id,
        "checker_decision",
        review_id=review.review_id,
        status=review.review_status,
    )

    try:
        previous_status = review.review_status

        result = manual_review_service.submit_checker_decision(
            db=db,
            review=review,
            checker_id=current_user.username,
            checker_decision=decision.checker_decision,
            checker_remarks=decision.checker_remarks,
        )

                # Preserve the original automated underwriting decision (REFER).
        # Record the checker outcome as a separate decision.

        original_reason_codes = [
            code.strip()
            for code in (credit_decision.reason_codes or "").split(",")
            if code.strip()
        ]

        checker_reason_code = (
            f"MANUAL_REVIEW_CHECKER_{decision.checker_decision}"
        )

        final_reason_codes = original_reason_codes.copy()
        if checker_reason_code not in final_reason_codes:
            final_reason_codes.append(checker_reason_code)

        final_decision_input = CreditDecisionOutput(
            application_id=application_id,
            credit_score=credit_decision.credit_score,
            risk_grade=credit_decision.risk_grade,
            probability_of_default=credit_decision.probability_of_default,
            affordability_score=credit_decision.affordability_score,
            repayment_propensity=credit_decision.repayment_propensity,
            fraud_score=credit_decision.fraud_score,
            income_stability_score=credit_decision.income_stability_score,
            risk_segment=credit_decision.risk_segment,
            recommended_amount=credit_decision.recommended_amount,
            recommended_tenure=credit_decision.recommended_tenure,
            recommended_emi=credit_decision.recommended_emi,
            foir=credit_decision.foir,
            decision=decision.checker_decision,
            confidence=credit_decision.confidence,
            reason_codes=final_reason_codes,
            model_version=credit_decision.model_version,
            policy_version=credit_decision.policy_version,
            effective_from=credit_decision.effective_from,
            effective_to=credit_decision.effective_to,
        )

        final_credit_decision = credit_decision_service.save_decision(
            db=db,
            decision=final_decision_input,
            commit=False,
            record_source="MANUAL_REVIEW_CHECKER",
        )

        # Reuse the original trace's evidence references and policy
        # evaluation. Do not claim that the model or policy ran again.
        original_trace = decision_trace_service.get_by_decision(
            db=db,
            decision_id=credit_decision.decision_id,
        )

        trace_metadata = (
            dict(original_trace.decision_metadata or {})
            if original_trace is not None
            else {}
        )

        trace_metadata.update(
            {
                "decision_source": "MANUAL_REVIEW_CHECKER",
                "original_decision_id": credit_decision.decision_id,
                "original_decision": "REFER",
                "manual_review_id": result.review_id,
                "maker_id": result.reviewer_id,
                "maker_recommendation": result.reviewer_decision,
                "checker_id": current_user.username,
                "checker_decision": decision.checker_decision,
                "policy_evaluation_status": "NOT_REEVALUATED",
                "original_decision_trace_id": (
                    original_trace.trace_id
                    if original_trace is not None
                    else None
                ),
            }
        )

        decision_trace_service.create_trace(
            db=db,
            application_id=application_id,
            decision_id=final_credit_decision.decision_id,
            feature_snapshot_id=(
                original_trace.feature_snapshot_id
                if original_trace is not None
                else None
            ),
            decision=decision.checker_decision,
            model_version=credit_decision.model_version,
            policy_version=credit_decision.policy_version,
            effective_from=credit_decision.effective_from,
            effective_to=credit_decision.effective_to,
            model_outputs=(
                original_trace.model_outputs
                if original_trace is not None
                else None
            ),
            policy_evaluation=(
                original_trace.policy_evaluation
                if original_trace is not None
                else None
            ),
            reason_codes=final_reason_codes,
            decision_metadata=trace_metadata,
            commit=False,
        )

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
            actor_reference=current_user.username,
            reviewer_id=result.reviewer_id,
            reviewer_decision=result.reviewer_decision,
            remarks=decision.checker_remarks,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            actor_type="USER",
            actor_reference=current_user.username,
            action="CREDIT_DECISION_CHECKER_FINALIZED",
            entity_type="CREDIT_DECISION",
            entity_reference=final_credit_decision.decision_id,
            description=(
                "The checker finalized the referred underwriting decision."
            ),
            previous_state="REFER",
            new_state=decision.checker_decision,
            request_reference=application_id,
            model_version=credit_decision.model_version,
            policy_version=credit_decision.policy_version,
        )

        db.commit()
        db.refresh(result)

        log_manual_review_event(
            logging.INFO,
            "completed",
            request,
            application_id,
            "checker_decision",
            review_id=result.review_id,
            status=result.review_status,
        )

        response_data = ManualReviewResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Manual review checker decision completed successfully.",
        )

    except ValueError as exc:
        db.rollback()

        log_manual_review_event(
            logging.WARNING,
            "failed",
            request,
            application_id,
            "checker_decision",
            review_id=review.review_id,
            status=review.review_status,
            error_code=str(exc),
        )

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        db.rollback()

        log_manual_review_event(
            level=logging.ERROR,
            event="failed",
            request=request,
            application_id=application_id,
            action="checker_decision",
            review_id=review.review_id,
            status=review.review_status,
            error_code="CHECKER_DECISION_FAILED",
        )

        logger.error(
            "manual_review_failed request_id=%s application_id=%s "
            "action=checker_decision error_type=unexpected",
            get_request_id(request),
            application_id,
        )

        raise HTTPException(
            status_code=500,
            detail="CHECKER_DECISION_FAILED",
        )


@router.get(
    "/{application_id}",
    response_model=ApiResponse[ManualReviewResponse],
)
def get_manual_review(
    application_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(
        require_roles(*MANUAL_REVIEW_READ_ROLES),
    ),
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
    response_model=ApiResponse[list[ManualReviewHistoryResponse]],
)
def get_manual_review_history(
    application_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(
        require_roles(*MANUAL_REVIEW_READ_ROLES),
    ),
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

    response_data = [
        ManualReviewHistoryResponse.model_validate(item)
        for item in result
    ]

    return success_response(
        request=request,
        data=response_data,
        message="Manual review history retrieved successfully.",
    )