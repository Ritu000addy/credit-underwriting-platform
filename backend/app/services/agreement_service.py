import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.agreement import Agreement

from backend.app.services.audit_log_service import audit_log_service
from backend.app.models.sanction import Sanction

class AgreementService:

    def create_agreement(
        self,
        db: Session,
        agreement_id: str,
        application_id: str,
        sanction_id: str,
        agreement_status: str,
        esign_status: str,
        agreement_reference: str | None = None,
        esign_provider: str | None = None,
        esign_reference: str | None = None,
        document_reference: str | None = None,
        failure_reason: str | None = None,
        initiated_at: datetime | None = None,
        signed_at: datetime | None = None,
    ) -> Agreement:

        sanction = db.get(Sanction, sanction_id)

        if sanction is None:
            raise ValueError("SANCTION_NOT_FOUND")

        if sanction.application_id != application_id:
            raise ValueError("SANCTION_APPLICATION_MISMATCH")

        if sanction.sanction_status != "APPROVED":
            raise ValueError("SANCTION_NOT_APPROVED")

        agreement = Agreement(
            agreement_id=agreement_id,
            application_id=application_id,
            sanction_id=sanction_id,
            agreement_reference=agreement_reference,
            agreement_status=agreement_status,
            esign_status=esign_status,
            esign_provider=esign_provider,
            esign_reference=esign_reference,
            document_reference=document_reference,
            failure_reason=failure_reason,
            initiated_at=initiated_at,
            signed_at=signed_at,
        )

        db.add(agreement)
        db.commit()
        db.refresh(agreement)

        return agreement

    def initiate_esign(
        self,
        db: Session,
        agreement: Agreement,
        esign_provider: str,
        esign_reference: str,
    ) -> Agreement:

        if agreement.agreement_status in {"COMPLETED", "CANCELLED"}:
            raise ValueError("AGREEMENT_NOT_ELIGIBLE_FOR_ESIGN")

        if agreement.esign_status == "INITIATED":
            raise ValueError("ESIGN_ALREADY_INITIATED")

        if agreement.esign_status == "SIGNED":
            raise ValueError("ESIGN_ALREADY_COMPLETED")

        agreement.esign_provider = esign_provider
        agreement.esign_reference = esign_reference
        agreement.esign_status = "INITIATED"
        agreement.agreement_status = "ACTIVE"
        agreement.initiated_at = datetime.utcnow()
        agreement.failure_reason = None

        db.commit()
        db.refresh(agreement)

        return agreement
    
    def complete_esign(
        self,
        db: Session,
        agreement: Agreement,
        esign_status: str,
        esign_reference: str | None = None,
        signed_at: datetime | None = None,
        failure_reason: str | None = None,
    ) -> Agreement:

        previous_agreement_status = agreement.agreement_status
        previous_esign_status = agreement.esign_status

        if agreement.esign_status != "INITIATED":
            raise ValueError("ESIGN_NOT_INITIATED")

        if esign_status == "SIGNED":
            agreement.esign_status = "SIGNED"
            agreement.agreement_status = "COMPLETED"
            agreement.esign_reference = esign_reference
            agreement.signed_at = signed_at or datetime.utcnow()
            agreement.failure_reason = None

        elif esign_status == "FAILED":
            agreement.esign_status = "FAILED"
            agreement.agreement_status = "CANCELLED"
            agreement.failure_reason = failure_reason

        else:
            raise ValueError(
                "Invalid eSign status. Expected SIGNED or FAILED."
            )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=agreement.application_id,
            actor_type="SYSTEM",
            action="ESIGN_COMPLETED" if esign_status == "SIGNED" else "ESIGN_FAILED",
            entity_type="AGREEMENT",
            entity_reference=agreement.agreement_id,
            description=(
                f"eSign status changed from "
                f"{previous_esign_status} to {agreement.esign_status}; "
                f"agreement status changed from "
                f"{previous_agreement_status} to {agreement.agreement_status}"
            ),
            previous_state=previous_agreement_status,
            new_state=agreement.agreement_status,
            request_reference=agreement.esign_reference,
        )

        db.commit()
        db.refresh(agreement)

        return agreement

agreement_service = AgreementService()