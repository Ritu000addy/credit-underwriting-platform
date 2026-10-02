from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.underwriting import UnderwritingResult
from backend.app.services.credit_decision_service import credit_decision_service
from backend.app.services.underwriting_pipeline import underwriting_pipeline
from backend.app.services.manual_review_service import manual_review_service

from backend.app.models.loan_application import LoanApplication


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
    result = underwriting_pipeline.process(
        application=application,
        borrower=borrower,
    )

    if result.decision is not None:
        credit_decision_service.save_decision(
            db=db,
            decision=result.decision,
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
        
        if result.decision.decision == "REFER":
            manual_review_service.create_review(
                db=db,
                application_id=application.application_id,
                review_reason=", ".join(result.decision.reason_codes),
            )

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