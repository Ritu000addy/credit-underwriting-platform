import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.disbursement import Disbursement
from backend.app.models.internal_ledger import InternalLedger

from backend.app.services.bank_routing_service import bank_routing_service
from backend.app.services.internal_ledger_service import internal_ledger_service
from backend.app.services.audit_log_service import audit_log_service


class DisbursementService:

    def create_disbursement(
        self,
        db: Session,
        disbursement_id: str,
        application_id: str,
        disbursement_amount: Decimal,
        status: str,
        idempotency_key: str | None = None,
        sanction_id: str | None = None,
        beneficiary_reference: str | None = None,
        bank_reference: str | None = None,
        payment_provider: str | None = None,
        failure_reason: str | None = None,
        processed_at=None,
    ) -> Disbursement:

        if status != "CREATED":
            raise ValueError(
                "INVALID_INITIAL_DISBURSEMENT_STATUS"
            )

        if idempotency_key:
            existing_disbursement = (
                db.query(Disbursement)
                .filter(
                    Disbursement.idempotency_key == idempotency_key
                )
                .first()
            )

            if existing_disbursement is not None:
                raise ValueError("DISBURSEMENT_ALREADY_EXISTS")

        disbursement = Disbursement(
            disbursement_id=disbursement_id,
            application_id=application_id,
            sanction_id=sanction_id,
            disbursement_amount=disbursement_amount,
            beneficiary_reference=beneficiary_reference,
            bank_reference=bank_reference,
            payment_provider=payment_provider,
            status=status,
            idempotency_key=idempotency_key,
            failure_reason=failure_reason,
            processed_at=processed_at,
        )

        db.add(disbursement)
        db.commit()
        db.refresh(disbursement)

        return disbursement

    def initiate_disbursement(
        self,
        db: Session,
        disbursement: Disbursement,
    ) -> Disbursement:

        previous_status = disbursement.status

        if disbursement.status != "CREATED":
            raise ValueError("DISBURSEMENT_NOT_ELIGIBLE_FOR_INITIATION")

        routing_result = bank_routing_service.route_disbursement(
            payment_provider=disbursement.payment_provider,
            disbursement_id=disbursement.disbursement_id,
        )

        if not routing_result.success:
            disbursement.status = "FAILED"
            disbursement.failure_reason = routing_result.failure_reason
            audit_log_service.log(
                db=db,
                audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
                application_id=disbursement.application_id,
                actor_type="SYSTEM",
                action="DISBURSEMENT_FAILED",
                entity_type="DISBURSEMENT",
                entity_reference=disbursement.disbursement_id,
                description=(
                    f"Disbursement initiation failed: "
                    f"{routing_result.failure_reason}"
                ),
                previous_state=previous_status,
                new_state="FAILED",
                request_reference=disbursement.disbursement_id,
            )
            db.commit()
            db.refresh(disbursement)
            return disbursement

        disbursement.status = "INITIATED"
        disbursement.bank_reference = routing_result.routing_reference

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=disbursement.application_id,
            actor_type="SYSTEM",
            action="DISBURSEMENT_INITIATED",
            entity_type="DISBURSEMENT",
            entity_reference=disbursement.disbursement_id,
            description="Disbursement initiated successfully.",
            previous_state=previous_status,
            new_state="INITIATED",
            request_reference=disbursement.disbursement_id,
        )

        existing_ledger_entry = (
            db.query(InternalLedger)
            .filter(
                InternalLedger.disbursement_id == disbursement.disbursement_id,
                InternalLedger.transaction_type == "DISBURSEMENT",
            )
            .first()
        )

        if existing_ledger_entry is None:
            internal_ledger_service.create_disbursement_entry(
                db=db,
                ledger_id=f"LEDGER-{uuid.uuid4().hex[:12].upper()}",
                application_id=disbursement.application_id,
                disbursement_id=disbursement.disbursement_id,
                transaction_amount=disbursement.disbursement_amount,
                internal_reference=f"LEDGER-{disbursement.disbursement_id}",
            )

        db.commit()
        db.refresh(disbursement)

        return disbursement

    def mark_processing(
        self,
        db: Session,
        disbursement: Disbursement,
    ) -> Disbursement:

        previous_status = disbursement.status

        if disbursement.status != "INITIATED":
            raise ValueError("DISBURSEMENT_NOT_INITIATED")

        disbursement.status = "PROCESSING"

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=disbursement.application_id,
            actor_type="SYSTEM",
            action="DISBURSEMENT_PROCESSING",
            entity_type="DISBURSEMENT",
            entity_reference=disbursement.disbursement_id,
            description="Disbursement moved to processing.",
            previous_state=previous_status,
            new_state="PROCESSING",
            request_reference=disbursement.disbursement_id,
        )

        db.commit()
        db.refresh(disbursement)

        return disbursement

    def process_disbursement(
        self,
        db: Session,
        disbursement: Disbursement,
        bank_reference: str | None = None,
    ) -> Disbursement:

        previous_status = disbursement.status

        if disbursement.status != "PROCESSING":
            raise ValueError(
                "DISBURSEMENT_NOT_READY_FOR_PROCESSING"
            )

        disbursement.status = "PROCESSED"
        disbursement.bank_reference = bank_reference
        disbursement.processed_at = datetime.utcnow()
        disbursement.failure_reason = None

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=disbursement.application_id,
            actor_type="SYSTEM",
            action="DISBURSEMENT_PROCESSED",
            entity_type="DISBURSEMENT",
            entity_reference=disbursement.disbursement_id,
            description="Disbursement processed successfully.",
            previous_state=previous_status,
            new_state="PROCESSED",
            request_reference=bank_reference,
        )

        db.commit()
        db.refresh(disbursement)

        return disbursement

    def fail_disbursement(
        self,
        db: Session,
        disbursement: Disbursement,
        failure_reason: str,
    ) -> Disbursement:

        previous_status = disbursement.status

        if disbursement.status not in {
            "CREATED",
            "INITIATED",
            "PROCESSING",
        }:
            raise ValueError("DISBURSEMENT_NOT_ELIGIBLE_FOR_FAILURE")

        disbursement.status = "FAILED"
        disbursement.failure_reason = failure_reason

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=disbursement.application_id,
            actor_type="SYSTEM",
            action="DISBURSEMENT_FAILED",
            entity_type="DISBURSEMENT",
            entity_reference=disbursement.disbursement_id,
            description=(
                f"Disbursement failed: {failure_reason}"
            ),
            previous_state=previous_status,
            new_state="FAILED",
            request_reference=disbursement.disbursement_id,
        )

        db.commit()
        db.refresh(disbursement)

        return disbursement

disbursement_service = DisbursementService()