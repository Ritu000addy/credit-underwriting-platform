from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.internal_ledger import InternalLedger


class InternalLedgerService:

    def create_disbursement_entry(
        self,
        db: Session,
        ledger_id: str,
        application_id: str,
        disbursement_id: str,
        transaction_amount: Decimal,
        internal_reference: str,
        transaction_date: datetime | None = None,
    ) -> InternalLedger:

        ledger_entry = InternalLedger(
            ledger_id=ledger_id,
            application_id=application_id,
            disbursement_id=disbursement_id,
            transaction_type="DISBURSEMENT",
            internal_reference=internal_reference,
            transaction_amount=transaction_amount,
            transaction_date=transaction_date or datetime.utcnow(),
            ledger_status="POSTED",
        )

        db.add(ledger_entry)
        db.flush()

        return ledger_entry


internal_ledger_service = InternalLedgerService()