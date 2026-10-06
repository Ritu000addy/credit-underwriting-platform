from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.database import SessionLocal
from backend.app.services.reconciliation_service import (
    reconciliation_service,
)


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def test_reconciliation_persistence():
    db = SessionLocal()

    try:
        reconciliation_id = unique("DEV-RECON")
        internal_reference = unique("DEV-REPAYMENT")
        external_reference = unique("REPAY-REF")

        reconciliation = (
            reconciliation_service.create_reconciliation(
                db=db,
                reconciliation_id=reconciliation_id,
                transaction_type="REPAYMENT",
                transaction_amount=Decimal("13327.32"),
                reconciliation_status="MATCHED",
                application_id="PERSIST-TEST-001",
                internal_reference=internal_reference,
                external_reference=external_reference,
                transaction_date=datetime(2026, 10, 25),
                reconciled_at=datetime(2026, 10, 25),
            )
        )

        assert (
            reconciliation.reconciliation_id
            == reconciliation_id
        )
        assert reconciliation.application_id == "PERSIST-TEST-001"
        assert reconciliation.transaction_type == "REPAYMENT"
        assert reconciliation.transaction_amount == Decimal(
            "13327.32"
        )
        assert reconciliation.reconciliation_status == "MATCHED"
        assert (
            reconciliation.internal_reference
            == internal_reference
        )
        assert (
            reconciliation.external_reference
            == external_reference
        )
        assert reconciliation.transaction_date == datetime(
            2026, 10, 25
        )
        assert reconciliation.reconciled_at == datetime(
            2026, 10, 25
        )

    finally:
        db.close()