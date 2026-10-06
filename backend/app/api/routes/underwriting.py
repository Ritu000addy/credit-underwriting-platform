import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.database import get_db
from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.underwriting import UnderwritingResult
from backend.app.services.credit_decision_service import credit_decision_service
from backend.app.services.underwriting_pipeline import underwriting_pipeline
from backend.app.services.manual_review_service import manual_review_service
from backend.app.services.audit_log_service import audit_log_service
from backend.app.services.underwriting_feature_snapshot_service import (
    underwriting_feature_snapshot_service,
)
from backend.app.services.decision_trace_service import (
    decision_trace_service,
)
from backend.app.services.review_exception_service import (
    review_exception_service,
)
from backend.app.services.policy_version_service import policy_version_service

from backend.app.models.loan_application import LoanApplication
from backend.app.models.customer import Customer


router = APIRouter(
    prefix="/underwriting",
    tags=["AI Credit Underwriting"],
)


@router.post(
    "/evaluate",
    response_model=UnderwritingResult,
)
def evaluate_application(
    application: ApplicationCreate,
    borrower: Borrower360,
    db: Session = Depends(get_db),
):

    application_record = db.get(
        LoanApplication,
        application.application_id,
    )

    if application_record is None:
        raise HTTPException(
            status_code=404,
            detail="APPLICATION_NOT_FOUND",
        )

    customer = db.get(
        Customer,
        application.customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="CUSTOMER_NOT_FOUND",
        )

    if application.customer_id != application_record.customer_id:
        raise HTTPException(
            status_code=400,
            detail="APPLICATION_CUSTOMER_MISMATCH",
        )

    if borrower.customer_id != application.customer_id:
        raise HTTPException(
            status_code=400,
            detail="BORROWER_CUSTOMER_MISMATCH",
        )

    try:
        policy_context = policy_version_service.get_policy_context(
            db=db,
            as_of=datetime.utcnow(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    result = underwriting_pipeline.process(
        application=application,
        borrower=borrower,
        policy_config=policy_context["policy_config"],
        policy_metadata=policy_context["policy_metadata"],
    )

    if result.decision is not None:
        saved_decision = credit_decision_service.save_decision(
            db=db,
            decision=result.decision,
        )

        feature_snapshot = underwriting_feature_snapshot_service.create_snapshot(
            db=db,
            application_id=result.decision.application_id,
            decision_id=saved_decision.decision_id,
            model_version=result.decision.model_version,
            features=result.decision.model_features or {},
        )

        decision_trace = decision_trace_service.create_trace(
            db=db,
            application_id=result.decision.application_id,
            decision_id=saved_decision.decision_id,
            feature_snapshot_id=feature_snapshot.feature_snapshot_id,
            decision=result.decision.decision,
            model_version=result.decision.model_version,
            policy_version=result.decision.policy_version,
            effective_from=result.decision.effective_from,
            effective_to=result.decision.effective_to,
            model_outputs={
                "credit_score": result.decision.credit_score,
                "risk_grade": result.decision.risk_grade,
                "probability_of_default": (
                    float(result.decision.probability_of_default)
                    if result.decision.probability_of_default is not None
                    else None
                ),
                "affordability_score": (
                    float(result.decision.affordability_score)
                    if result.decision.affordability_score is not None
                    else None
                ),
                "repayment_propensity": (
                    float(result.decision.repayment_propensity)
                    if result.decision.repayment_propensity is not None
                    else None
                ),
                "fraud_score": (
                    float(result.decision.fraud_score)
                    if result.decision.fraud_score is not None
                    else None
                ),
                "income_stability_score": (
                    float(result.decision.income_stability_score)
                    if result.decision.income_stability_score is not None
                    else None
                ),
                "risk_segment": result.decision.risk_segment,
                "recommended_amount": (
                    float(result.decision.recommended_amount)
                    if result.decision.recommended_amount is not None
                    else None
                ),
                "recommended_tenure": result.decision.recommended_tenure,
                "recommended_emi": (
                    float(result.decision.recommended_emi)
                    if result.decision.recommended_emi is not None
                    else None
                ),
                "foir": (
                    float(result.decision.foir)
                    if result.decision.foir is not None
                    else None
                ),
                "confidence": (
                    float(result.decision.confidence)
                    if result.decision.confidence is not None
                    else None
                ),
            },
            policy_evaluation=[
                rule.model_dump()
                for rule in result.decision.policy_checks
            ],
            reason_codes=result.decision.reason_codes,
            decision_metadata={
                "feature_version": feature_snapshot.feature_version,
            },
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.decision.application_id,
            actor_type="SYSTEM",
            action="FEATURE_SNAPSHOT_CREATED",
            entity_type="UNDERWRITING_FEATURE_SNAPSHOT",
            entity_reference=feature_snapshot.feature_snapshot_id,
            description="Material underwriting feature snapshot created.",
            previous_state=None,
            new_state="CREATED",
            request_reference=result.decision.application_id,
            model_version=result.decision.model_version,
            policy_version=result.decision.policy_version,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.decision.application_id,
            actor_type="SYSTEM",
            action="RISK_ASSESSMENT_COMPLETED",
            entity_type="CREDIT_RISK_ASSESSMENT",
            entity_reference=saved_decision.decision_id,
            description="Credit risk model assessment completed.",
            previous_state=None,
            new_state="COMPLETED",
            request_reference=result.decision.application_id,
            model_version=result.decision.model_version,
            policy_version=result.decision.policy_version,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.decision.application_id,
            actor_type="SYSTEM",
            action="POLICY_EVALUATION_COMPLETED",
            entity_type="POLICY_EVALUATION",
            entity_reference=saved_decision.decision_id,
            description=(
                f"Policy evaluation completed with status "
                f"{result.decision.decision}."
            ),
            previous_state=None,
            new_state=result.decision.decision,
            request_reference=result.decision.application_id,
            model_version=result.decision.model_version,
            policy_version=result.decision.policy_version,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.decision.application_id,
            actor_type="SYSTEM",
            action="DECISION_TRACE_CREATED",
            entity_type="DECISION_TRACE",
            entity_reference=decision_trace.trace_id,
            description="Complete underwriting decision trace created.",
            previous_state=None,
            new_state="CREATED",
            request_reference=result.decision.application_id,
            model_version=result.decision.model_version,
            policy_version=result.decision.policy_version,
        )

        application_record = db.get(
            LoanApplication,
            result.decision.application_id,
        )

        if application_record is not None:
            application_record.status = {
                "APPROVE": "APPROVED",
                "REFER": "REFERRED",
                "REJECT": "REJECTED",
            }[result.decision.decision]

            db.commit()
            db.refresh(application_record)

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.decision.application_id,
            actor_type="SYSTEM",
            action="UNDERWRITING_DECISION",
            entity_type="CREDIT_DECISION",
            entity_reference=saved_decision.decision_id,
            description=(
                f"AI underwriting decision generated: "
                f"{result.decision.decision}"
            ),
            previous_state="UNDERWRITING_PENDING",
            new_state=result.decision.decision,
            request_reference=result.decision.application_id,
            model_version=result.decision.model_version,
            policy_version=result.decision.policy_version,
        )
        
        if result.decision.decision == "REFER":
            manual_review = manual_review_service.create_review(
                db=db,
                application_id=application.application_id,
                review_reason=", ".join(result.decision.reason_codes),
            )

            audit_log_service.log(
                db=db,
                audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
                application_id=result.decision.application_id,
                actor_type="SYSTEM",
                action="MANUAL_REVIEW_CREATED",
                entity_type="MANUAL_REVIEW",
                entity_reference=manual_review.review_id,
                description=(
                    "Manual review created because underwriting decision "
                    "was REFER."
                ),
                previous_state="REFER",
                new_state="OPEN",
                request_reference=result.decision.application_id,
                model_version=result.decision.model_version,
                policy_version=result.decision.policy_version,
            )

            review_exception = review_exception_service.create_exception(
                db=db,
                review_id=manual_review.review_id,
                application_id=application.application_id,
                exception_type="UNDERWRITING_REFER",
                description=(
                    "Application referred for manual credit review. "
                    f"Reason codes: {', '.join(result.decision.reason_codes)}"
                ),
                created_by="SYSTEM",
            )

            audit_log_service.log(
                db=db,
                audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
                application_id=result.decision.application_id,
                actor_type="SYSTEM",
                action="REVIEW_EXCEPTION_CREATED",
                entity_type="REVIEW_EXCEPTION",
                entity_reference=review_exception.exception_id,
                description=(
                    "Review exception created for REFER underwriting decision."
                ),
                previous_state="REFER",
                new_state="OPEN",
                request_reference=result.decision.application_id,
                model_version=result.decision.model_version,
                policy_version=result.decision.policy_version,
            )

            db.commit()
            
    return result

@router.get("/{application_id}")
def get_underwriting_result(
    application_id: str,
    db: Session = Depends(get_db),
):
    result = credit_decision_service.get_decision(
        db=db,
        application_id=application_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Underwriting result not found",
        )

    return {
        "decision_id": result.decision_id,
        "application_id": result.application_id,
        "credit_score": result.credit_score,
        "risk_grade": result.risk_grade,
        "probability_of_default": result.probability_of_default,
        "affordability_score": result.affordability_score,
        "repayment_propensity": result.repayment_propensity,
        "fraud_score": result.fraud_score,
        "income_stability_score": result.income_stability_score,
        "risk_segment": result.risk_segment,
        "recommended_amount": result.recommended_amount,
        "recommended_tenure": result.recommended_tenure,
        "recommended_emi": result.recommended_emi,
        "foir": result.foir,
        "decision": result.decision,
        "confidence": result.confidence,
        "reason_codes": (
            result.reason_codes.split(",")
            if result.reason_codes
            else []
        ),
        "model_version": result.model_version,
        "policy_version": result.policy_version,
        "created_at": result.created_at,
    }