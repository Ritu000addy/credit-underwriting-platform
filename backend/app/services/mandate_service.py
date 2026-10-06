import uuid
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.models.mandate import Mandate
from backend.app.models.agreement import Agreement

from backend.app.services.audit_log_service import audit_log_service


class MandateService:

    def create_mandate(
        self,
        db: Session,
        mandate_id: str,
        application_id: str,
        status: str,
        mandate_reference: str | None = None,
        mandate_type: str | None = None,
        provider: str | None = None,
        failure_reason: str | None = None,
        completed_at=None,
    ) -> Mandate:

        agreement = (
            db.query(Agreement)
            .filter(
                Agreement.application_id == application_id,
                Agreement.agreement_status == "COMPLETED",
                Agreement.esign_status == "SIGNED",
            )
            .order_by(Agreement.signed_at.desc())
            .first()
        )

        if agreement is None:
            raise ValueError("AGREEMENT_NOT_COMPLETED")

        if status != "CREATED":
            raise ValueError(
                "INVALID_INITIAL_MANDATE_STATUS"
            )

        existing_mandate = (
            db.query(Mandate)
            .filter(Mandate.application_id == application_id)
            .first()
        )

        if existing_mandate is not None:
            raise ValueError("MANDATE_ALREADY_EXISTS")

        mandate = Mandate(
            mandate_id=mandate_id,
            application_id=application_id,
            mandate_reference=mandate_reference,
            mandate_type=mandate_type,
            provider=provider,
            status=status,
            failure_reason=failure_reason,
            completed_at=completed_at,
        )

        db.add(mandate)
        db.commit()
        db.refresh(mandate)

        return mandate

    def initiate_mandate(
        self,
        db: Session,
        mandate: Mandate,
    ) -> Mandate:

        if mandate.status != "CREATED":
            raise ValueError(
                f"MANDATE_NOT_ELIGIBLE_FOR_INITIATION:{mandate.status}"
            )

        mandate.status = "INITIATED"
        mandate.initiated_at = datetime.utcnow()
        mandate.failure_reason = None

        db.commit()
        db.refresh(mandate)

        return mandate

    def complete_mandate(
        self,
        db: Session,
        mandate: Mandate,
        status: str,
        failure_reason: str | None = None,
        completed_at: datetime | None = None,
    ) -> Mandate:

        previous_status = mandate.status

        if mandate.status != "INITIATED":
            raise ValueError("MANDATE_NOT_INITIATED")

        if status == "COMPLETED":
            mandate.status = "COMPLETED"
            mandate.completed_at = completed_at or datetime.utcnow()
            mandate.failure_reason = None

        elif status == "FAILED":
            mandate.status = "FAILED"
            mandate.failure_reason = failure_reason
            mandate.completed_at = None

        else:
            raise ValueError(
                "Invalid mandate status. Expected COMPLETED or FAILED."
            )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=mandate.application_id,
            actor_type="SYSTEM",
            action="MANDATE_COMPLETED" if status == "COMPLETED" else "MANDATE_FAILED",
            entity_type="MANDATE",
            entity_reference=mandate.mandate_id,
            description=(
                f"Mandate status changed from "
                f"{previous_status} to {mandate.status}"
            ),
            previous_state=previous_status,
            new_state=mandate.status,
            request_reference=mandate.mandate_reference,
        )

        db.commit()
        db.refresh(mandate)

        return mandate

mandate_service = MandateService()