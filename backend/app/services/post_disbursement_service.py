from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.services.sanction_service import sanction_service
from backend.app.services.mandate_service import mandate_service
from backend.app.services.disbursement_service import disbursement_service
from backend.app.services.repayment_schedule_service import (
    repayment_schedule_service,
)
from backend.app.services.repayment_service import repayment_service
from backend.app.services.reconciliation_service import reconciliation_service
from backend.app.services.collection_service import collection_service
from backend.app.services.agreement_service import agreement_service

class PostDisbursementService:

    def create_sanction(
        self,
        db: Session,
        application_id: str,
        sanction_id: str,
        sanctioned_amount: Decimal,
        sanctioned_tenure: int,
        sanctioned_emi: Decimal | None = None,
        interest_rate: Decimal | None = None,
        approval_authority: str | None = None,
        terms_and_conditions: str | None = None,
        expires_at=None,
    ):

        return sanction_service.create_sanction(
            db=db,
            sanction_id=sanction_id,
            application_id=application_id,
            sanctioned_amount=sanctioned_amount,
            sanctioned_tenure=sanctioned_tenure,
            sanctioned_emi=sanctioned_emi,
            interest_rate=interest_rate,
            sanction_status="APPROVED",
            approval_authority=approval_authority,
            terms_and_conditions=terms_and_conditions,
            expires_at=expires_at,
        )

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
        initiated_at=None,
        signed_at=None,
    ):

        return agreement_service.create_agreement(
            db=db,
            agreement_id=agreement_id,
            application_id=application_id,
            sanction_id=sanction_id,
            agreement_status=agreement_status,
            esign_status=esign_status,
            agreement_reference=agreement_reference,
            esign_provider=esign_provider,
            esign_reference=esign_reference,
            document_reference=document_reference,
            failure_reason=failure_reason,
            initiated_at=initiated_at,
            signed_at=signed_at,
        )
    

    def create_mandate(
        self,
        db: Session,
        application_id: str,
        mandate_id: str,
        status: str,
        mandate_reference: str | None = None,
        mandate_type: str | None = None,
        provider: str | None = None,
        failure_reason: str | None = None,
        completed_at=None,
    ):

        return mandate_service.create_mandate(
            db=db,
            mandate_id=mandate_id,
            application_id=application_id,
            status=status,
            mandate_reference=mandate_reference,
            mandate_type=mandate_type,
            provider=provider,
            failure_reason=failure_reason,
            completed_at=completed_at,
        )

    def create_disbursement(
        self,
        db: Session,
        application_id: str,
        disbursement_id: str,
        disbursement_amount: Decimal,
        sanction_id: str | None = None,
        beneficiary_reference: str | None = None,
        bank_reference: str | None = None,
        payment_provider: str | None = None,
        failure_reason: str | None = None,
        processed_at=None,
    ):
        return disbursement_service.create_disbursement(
            db=db,
            disbursement_id=disbursement_id,
            application_id=application_id,
            disbursement_amount=disbursement_amount,
            status="CREATED",
            sanction_id=sanction_id,
            beneficiary_reference=beneficiary_reference,
            bank_reference=bank_reference,
            payment_provider=payment_provider,
            failure_reason=failure_reason,
            processed_at=processed_at,
        )

    def create_repayment_schedule(
        self,
        db: Session,
        repayment_schedule_id: str,
        application_id: str,
        disbursement_id: str,
        installment_number: int,
        due_date,
        principal_due: Decimal,
        interest_due: Decimal,
        total_due: Decimal,
        outstanding_principal: Decimal,
        status: str = "PENDING",
        paid_at=None,
    ):

        return repayment_schedule_service.create_installment(
            db=db,
            repayment_schedule_id=repayment_schedule_id,
            application_id=application_id,
            disbursement_id=disbursement_id,
            installment_number=installment_number,
            due_date=due_date,
            principal_due=principal_due,
            interest_due=interest_due,
            total_due=total_due,
            outstanding_principal=outstanding_principal,
            status=status,
            paid_at=paid_at,
        )
    
    def create_repayment(
        self,
        db: Session,
        repayment_id: str,
        application_id: str,
        repayment_amount: Decimal,
        status: str,
        repayment_schedule_id: str | None = None,
        repayment_reference: str | None = None,
        payment_mode: str | None = None,
        payment_provider: str | None = None,
        principal_allocated: Decimal | None = None,
        interest_allocated: Decimal | None = None,
        failure_reason: str | None = None,
        paid_at=None,
    ):

        return repayment_service.create_repayment(
            db=db,
            repayment_id=repayment_id,
            application_id=application_id,
            repayment_amount=repayment_amount,
            status=status,
            repayment_schedule_id=repayment_schedule_id,
            repayment_reference=repayment_reference,
            payment_mode=payment_mode,
            payment_provider=payment_provider,
            principal_allocated=principal_allocated,
            interest_allocated=interest_allocated,
            failure_reason=failure_reason,
            paid_at=paid_at,
        )

    def create_reconciliation(
        self,
        db: Session,
        reconciliation_id: str,
        transaction_type: str,
        transaction_amount: Decimal,
        reconciliation_status: str,
        application_id: str | None = None,
        internal_reference: str | None = None,
        external_reference: str | None = None,
        transaction_date=None,
        mismatch_reason: str | None = None,
        reconciled_at=None,
    ):

        return reconciliation_service.create_reconciliation(
            db=db,
            reconciliation_id=reconciliation_id,
            transaction_type=transaction_type,
            transaction_amount=transaction_amount,
            reconciliation_status=reconciliation_status,
            application_id=application_id,
            internal_reference=internal_reference,
            external_reference=external_reference,
            transaction_date=transaction_date,
            mismatch_reason=mismatch_reason,
            reconciled_at=reconciled_at,
        )
    
    def create_collection(
        self,
        db: Session,
        collection_id: str,
        application_id: str,
        collection_type: str,
        due_amount: Decimal,
        collected_amount: Decimal,
        outstanding_amount: Decimal,
        days_past_due: int,
        status: str,
        repayment_schedule_id: str | None = None,
        collection_reference: str | None = None,
        collection_channel: str | None = None,
        remarks: str | None = None,
        collected_at=None,
    ):

        return collection_service.create_collection(
            db=db,
            collection_id=collection_id,
            application_id=application_id,
            collection_type=collection_type,
            due_amount=due_amount,
            collected_amount=collected_amount,
            outstanding_amount=outstanding_amount,
            days_past_due=days_past_due,
            status=status,
            repayment_schedule_id=repayment_schedule_id,
            collection_reference=collection_reference,
            collection_channel=collection_channel,
            remarks=remarks,
            collected_at=collected_at,
        )

post_disbursement_service = PostDisbursementService()