import uuid

from datetime import datetime
from dataclasses import dataclass

from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.disbursement import Disbursement
from backend.app.models.reconciliation import Reconciliation
from backend.app.models.operations_queue import OperationsQueue
from backend.app.models.internal_ledger import InternalLedger

from backend.app.services.audit_log_service import audit_log_service


@dataclass
class ReconciliationMatchResult:
    status: str
    disbursement_id: str
    bank_reference: str | None = None
    bank_amount: Decimal | None = None
    expected_amount: Decimal | None = None
    mismatch_reason: str | None = None

class ReconciliationService:

    def match_disbursement(
        self,
        disbursement_id: str,
        expected_amount: Decimal,
        bank_reference: str | None,
        bank_amount: Decimal | None,
        expected_bank_reference: str | None,
    ) -> ReconciliationMatchResult:

        if bank_reference is None:
            return ReconciliationMatchResult(
                status="PENDING",
                disbursement_id=disbursement_id,
                bank_reference=None,
                bank_amount=bank_amount,
                expected_amount=expected_amount,
                mismatch_reason="BANK_REFERENCE_NOT_AVAILABLE",
            )

        if expected_bank_reference is not None:
            if bank_reference != expected_bank_reference:
                return ReconciliationMatchResult(
                    status="MISMATCH",
                    disbursement_id=disbursement_id,
                    bank_reference=bank_reference,
                    bank_amount=bank_amount,
                    expected_amount=expected_amount,
                    mismatch_reason="BANK_REFERENCE_MISMATCH",
                )

        if bank_amount is None:
            return ReconciliationMatchResult(
                status="PENDING",
                disbursement_id=disbursement_id,
                bank_reference=bank_reference,
                bank_amount=None,
                expected_amount=expected_amount,
                mismatch_reason="BANK_AMOUNT_NOT_AVAILABLE",
            )

        if bank_amount != expected_amount:
            return ReconciliationMatchResult(
                status="MISMATCH",
                disbursement_id=disbursement_id,
                bank_reference=bank_reference,
                bank_amount=bank_amount,
                expected_amount=expected_amount,
                mismatch_reason="AMOUNT_MISMATCH",
            )

        return ReconciliationMatchResult(
            status="MATCHED",
            disbursement_id=disbursement_id,
            bank_reference=bank_reference,
            bank_amount=bank_amount,
            expected_amount=expected_amount,
            )

    def reconcile_disbursement(
        self,
        db: Session,
        disbursement_id: str,
        bank_reference: str | None,
        bank_amount: Decimal | None,
    ) -> ReconciliationMatchResult:

        disbursement = (
            db.query(Disbursement)
            .filter(
                Disbursement.disbursement_id == disbursement_id
            )
            .with_for_update()
            .first()
        )

        if disbursement is None:
            return ReconciliationMatchResult(
                status="MISMATCH",
                disbursement_id=disbursement_id,
                bank_reference=bank_reference,
                bank_amount=bank_amount,
                expected_amount=None,
                mismatch_reason="DISBURSEMENT_NOT_FOUND",
            )

        if disbursement.status != "PROCESSED":
            return ReconciliationMatchResult(
                status="MISMATCH",
                disbursement_id=disbursement_id,
                bank_reference=bank_reference,
                bank_amount=bank_amount,
                expected_amount=None,
                mismatch_reason="DISBURSEMENT_NOT_PROCESSED",
            )

        ledger_entry = (
        db.query(InternalLedger)
        .filter(
            InternalLedger.disbursement_id == disbursement_id,
            InternalLedger.transaction_type == "DISBURSEMENT",
        )
        .first()
    )

        if ledger_entry is None:
            return ReconciliationMatchResult(
                status="MISMATCH",
                disbursement_id=disbursement_id,
                bank_reference=bank_reference,
                bank_amount=bank_amount,
                expected_amount=None,
                mismatch_reason="INTERNAL_LEDGER_ENTRY_NOT_FOUND",
            )

        expected_amount = ledger_entry.transaction_amount

        closed_reconciliation = (
            db.query(Reconciliation)
            .filter(
                Reconciliation.disbursement_id == disbursement_id,
                Reconciliation.transaction_type == "DISBURSEMENT",
                Reconciliation.reconciliation_status == "CLOSED",
            )
            .first()
        )

        if closed_reconciliation is not None:
            return ReconciliationMatchResult(
                status="CLOSED",
                disbursement_id=disbursement_id,
                bank_reference=closed_reconciliation.external_reference,
                bank_amount=closed_reconciliation.transaction_amount,
                expected_amount=expected_amount,
                mismatch_reason=None,
            )

        existing_reconciliation = (
            db.query(Reconciliation)
            .filter(
                Reconciliation.disbursement_id == disbursement_id,
                Reconciliation.transaction_type == "DISBURSEMENT",
            )
            .first()
        )

        if (
            existing_reconciliation is not None
            and existing_reconciliation.external_reference == bank_reference
            and existing_reconciliation.transaction_amount == bank_amount
        ):
            return ReconciliationMatchResult(
                status=existing_reconciliation.reconciliation_status,
                disbursement_id=disbursement_id,
                bank_reference=existing_reconciliation.external_reference,
                bank_amount=existing_reconciliation.transaction_amount,
                expected_amount=expected_amount,
                mismatch_reason=existing_reconciliation.mismatch_reason,
            )

        result = self.match_disbursement(
            disbursement_id=disbursement.disbursement_id,
            expected_amount=expected_amount,
            bank_reference=bank_reference,
            bank_amount=bank_amount,
            expected_bank_reference=disbursement.bank_reference,
        )

        reconciliation_id = f"RECON-{uuid.uuid4().hex[:12].upper()}"

        self.create_reconciliation(
            db=db,
            reconciliation_id=reconciliation_id,
            application_id=disbursement.application_id,
            disbursement_id=disbursement.disbursement_id,
            transaction_type="DISBURSEMENT",
            transaction_amount=(
                result.bank_amount
                if result.bank_amount is not None
                else expected_amount
            ),
            reconciliation_status=result.status,
            internal_reference=ledger_entry.internal_reference,
            external_reference=result.bank_reference,
            transaction_date=ledger_entry.transaction_date,
            mismatch_reason=result.mismatch_reason,
            reconciled_at=(
                datetime.utcnow()
                if result.status == "MATCHED"
                else None
            ),
            commit_transaction=False,
        )

        if result.status == "MISMATCH":
            self.create_operations_queue(
                db=db,
                reconciliation_id=reconciliation_id,
                disbursement_id=disbursement.disbursement_id,
                queue_type="RECONCILIATION_MISMATCH",
                reason=result.mismatch_reason,
                commit_transaction=False,
            )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=disbursement.application_id,
            actor_type="SYSTEM",
            action="RECONCILIATION_COMPLETED",
            entity_type="RECONCILIATION",
            entity_reference=reconciliation_id,
            description=(
                f"Reconciliation completed with status "
                f"{result.status}"
                + (
                    f" and reason {result.mismatch_reason}"
                    if result.mismatch_reason
                    else ""
                )
            ),
            previous_state="PENDING",
            new_state=result.status,
            request_reference=disbursement.disbursement_id,
        )

        db.commit()

        return result

    def close_reconciliation(
        self,
        db: Session,
        reconciliation_id: str,
    ) -> Reconciliation:

        reconciliation = db.get(
            Reconciliation,
            reconciliation_id,
        )

        if reconciliation is None:
            raise ValueError("RECONCILIATION_NOT_FOUND")

        previous_status = reconciliation.reconciliation_status

        if reconciliation.reconciliation_status == "CLOSED":
            raise ValueError("RECONCILIATION_ALREADY_CLOSED")

        if reconciliation.reconciliation_status != "MATCHED":
            raise ValueError("RECONCILIATION_NOT_MATCHED")

        reconciliation.reconciliation_status = "CLOSED"
        reconciliation.reconciled_at = (
            reconciliation.reconciled_at or datetime.utcnow()
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=reconciliation.application_id,
            actor_type="SYSTEM",
            action="RECONCILIATION_CLOSED",
            entity_type="RECONCILIATION",
            entity_reference=reconciliation.reconciliation_id,
            description="Reconciliation closed successfully",
            previous_state=previous_status,
            new_state="CLOSED",
            request_reference=reconciliation.disbursement_id,
        )

        db.commit()
        db.refresh(reconciliation)

        return reconciliation

    def create_operations_queue(
        self,
        db: Session,
        reconciliation_id: str,
        disbursement_id: str | None,
        queue_type: str,
        reason: str | None = None,
        commit_transaction: bool = True,
    ) -> OperationsQueue:

        queue_item = OperationsQueue(
            queue_id=f"OPS-{reconciliation_id}",
            reconciliation_id=reconciliation_id,
            disbursement_id=disbursement_id,
            queue_type=queue_type,
            queue_status="OPEN",
            reason=reason,
        )

        db.add(queue_item)
        db.flush()

        if commit_transaction:
            db.commit()
            db.refresh(queue_item)

        return queue_item

    def update_operations_queue_status(
        self,
        db: Session,
        queue_id: str,
        queue_status: str,
    ) -> OperationsQueue:

        queue_item = db.get(
            OperationsQueue,
            queue_id,
        )

        if queue_item is None:
            raise ValueError("OPERATIONS_QUEUE_NOT_FOUND")

        previous_status = queue_item.queue_status

        allowed_transitions = {
            "OPEN": {"IN_PROGRESS"},
            "IN_PROGRESS": {"RESOLVED"},
            "RESOLVED": set(),
        }

        current_status = queue_item.queue_status

        if current_status not in allowed_transitions:
            raise ValueError(
                f"INVALID_OPERATIONS_QUEUE_STATE:{current_status}"
            )

        if queue_status not in {
            "OPEN",
            "IN_PROGRESS",
            "RESOLVED",
        }:
            raise ValueError(
                "INVALID_OPERATIONS_QUEUE_STATUS"
            )

        if queue_status not in allowed_transitions[current_status]:
            raise ValueError(
                f"OPERATIONS_QUEUE_INVALID_TRANSITION:"
                f"{current_status}->{queue_status}"
            )

        queue_item.queue_status = queue_status

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="SYSTEM",
            action="OPERATIONS_QUEUE_STATUS_CHANGED",
            entity_type="OPERATIONS_QUEUE",
            entity_reference=queue_item.queue_id,
            description=(
                f"Operations queue status changed from "
                f"{previous_status} to {queue_status}"
            ),
            previous_state=previous_status,
            new_state=queue_status,
            request_reference=queue_item.disbursement_id
            or queue_item.reconciliation_id,
        )

        db.commit()
        db.refresh(queue_item)

        return queue_item

    def create_reconciliation(
        self,
        db: Session,
        reconciliation_id: str,
        transaction_type: str,
        transaction_amount: Decimal,
        reconciliation_status: str,
        application_id: str | None = None,
        disbursement_id: str | None = None,
        internal_reference: str | None = None,
        external_reference: str | None = None,
        transaction_date: datetime | None = None,
        mismatch_reason: str | None = None,
        reconciled_at: datetime | None = None,
        commit_transaction: bool = True,
    ) -> Reconciliation:

        if transaction_type not in {
            "DISBURSEMENT",
            "REPAYMENT",
        }:
            raise ValueError(
                "INVALID_RECONCILIATION_TRANSACTION_TYPE"
            )

        if reconciliation_status not in {
            "PENDING",
            "MATCHED",
            "MISMATCH",
            "CLOSED",
        }:
            raise ValueError(
                "INVALID_RECONCILIATION_STATUS"
            )

        if reconciliation_status == "CLOSED":
            if reconciled_at is None:
                raise ValueError(
                    "CLOSED_RECONCILIATION_REQUIRES_RECONCILED_AT"
                )

        if reconciliation_status == "MATCHED":
            if reconciled_at is None:
                raise ValueError(
                    "MATCHED_RECONCILIATION_REQUIRES_RECONCILED_AT"
                )

        reconciliation = Reconciliation(
            reconciliation_id=reconciliation_id,
            application_id=application_id,
            disbursement_id=disbursement_id,
            transaction_type=transaction_type,
            internal_reference=internal_reference,
            external_reference=external_reference,
            transaction_amount=transaction_amount,
            transaction_date=transaction_date,
            reconciliation_status=reconciliation_status,
            mismatch_reason=mismatch_reason,
            reconciled_at=reconciled_at,
        )

        db.add(reconciliation)
        db.flush()

        if commit_transaction:
            db.commit()
            db.refresh(reconciliation)

        return reconciliation


reconciliation_service = ReconciliationService()