from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.agreement import Agreement


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

        db.commit()
        db.refresh(agreement)

        return agreement

agreement_service = AgreementService()