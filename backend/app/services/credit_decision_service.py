import uuid
from sqlalchemy.orm import Session

from backend.app.models.credit_decision import CreditDecision
from backend.app.schemas.credit_decision import CreditDecisionOutput


class CreditDecisionService:

    def save_decision(
        self,
        db: Session,
        decision: CreditDecisionOutput,
    ) -> CreditDecision:

        credit_decision = CreditDecision(
            decision_id=f"DEC-{uuid.uuid4().hex[:12].upper()}",
            application_id=decision.application_id,

            # Core Risk Outputs
            credit_score=decision.credit_score,
            risk_grade=decision.risk_grade,
            probability_of_default=decision.probability_of_default,

            # AI/ML Risk Indicators
            affordability_score=decision.affordability_score,
            repayment_propensity=decision.repayment_propensity,
            fraud_score=decision.fraud_score,
            income_stability_score=decision.income_stability_score,

            # Risk Segmentation
            risk_segment=decision.risk_segment,

            # Loan Recommendation
            recommended_amount=decision.recommended_amount,
            recommended_tenure=decision.recommended_tenure,
            recommended_emi=decision.recommended_emi,

            # Affordability
            foir=decision.foir,

            # Final Decision
            decision=decision.decision,
            confidence=decision.confidence,

            # Explainability
            reason_codes=",".join(decision.reason_codes),

            # Model Governance
            model_version=decision.model_version,
            policy_version=decision.policy_version,
            effective_from=decision.effective_from,
            effective_to=decision.effective_to,
        )

        db.add(credit_decision)
        db.commit()
        db.refresh(credit_decision)

        return credit_decision

    def get_decision(
        self,
        db: Session,
        application_id: str,
    ) -> CreditDecision | None:

        return (
            db.query(CreditDecision)
            .filter(
                CreditDecision.application_id == application_id
            )
            .order_by(CreditDecision.created_at.desc())
            .first()
        )

credit_decision_service = CreditDecisionService()