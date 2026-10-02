import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.sanction import Sanction
from backend.app.models.credit_decision import CreditDecision

from backend.app.services.audit_log_service import audit_log_service


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

        existing_sanction = (
            db.query(Sanction)
            .filter(Sanction.application_id == application_id)
            .first()
        )

        if existing_sanction is not None:
            raise ValueError("SANCTION_ALREADY_EXISTS")

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

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            actor_type="SYSTEM",
            action="SANCTION_CREATED",
            entity_type="SANCTION",
            entity_reference=sanction_id,
            description=(
                f"Sanction created for amount "
                f"{sanctioned_amount} with status "
                f"{sanction_status}"
            ),
            previous_state="APPROVED",
            new_state=sanction_status,
            request_reference=application_id,
        )
        
        db.commit()
        db.refresh(sanction)

        return sanction


sanction_service = SanctionService()