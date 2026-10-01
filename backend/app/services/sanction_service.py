from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.sanction import Sanction
from backend.app.models.credit_decision import CreditDecision


class SanctionService:

    def create_sanction(
        self,
        db: Session,
        sanction_id: str,
        application_id: str,
        sanctioned_amount: Decimal,
        sanctioned_tenure: int,
        sanction_status: str,
        sanctioned_emi: Decimal | None = None,
        interest_rate: Decimal | None = None,
        approval_authority: str | None = None,
        terms_and_conditions: str | None = None,
        expires_at=None,
    ) -> Sanction:

        credit_decision = (
            db.query(CreditDecision)
            .filter(
                CreditDecision.application_id == application_id
            )
            .order_by(CreditDecision.created_at.desc())
            .first()
        )

        if credit_decision is None:
            raise ValueError("CREDIT_DECISION_NOT_FOUND")

        if credit_decision.decision != "APPROVE":
            raise ValueError(
                f"APPLICATION_NOT_APPROVED: {credit_decision.decision}"
            )

        sanction = Sanction(
            sanction_id=sanction_id,
            application_id=application_id,
            sanctioned_amount=sanctioned_amount,
            sanctioned_tenure=sanctioned_tenure,
            sanctioned_emi=sanctioned_emi,
            interest_rate=interest_rate,
            sanction_status=sanction_status,
            approval_authority=approval_authority,
            terms_and_conditions=terms_and_conditions,
            expires_at=expires_at,
        )

        db.add(sanction)
        db.commit()
        db.refresh(sanction)

        return sanction


sanction_service = SanctionService()