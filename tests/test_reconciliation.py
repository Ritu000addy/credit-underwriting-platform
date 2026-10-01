from datetime import datetime
from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.services.reconciliation_service import reconciliation_service


db = SessionLocal()

try:
    reconciliation = reconciliation_service.create_reconciliation(
        db=db,
        reconciliation_id="DEV-ORCH-RECON-001",
        transaction_type="REPAYMENT",
        transaction_amount=Decimal("13327.32"),
        reconciliation_status="MATCHED",
        application_id="PERSIST-TEST-001",
        internal_reference="DEV-ORCH-REPAYMENT-PAY-001",
        external_reference="REPAY-REF-001",
        transaction_date=datetime(2026, 10, 25),
        reconciled_at=datetime(2026, 10, 25),
    )

    print("RECONCILIATION CREATED")
    print("reconciliation_id:", reconciliation.reconciliation_id)
    print("application_id:", reconciliation.application_id)
    print("transaction_type:", reconciliation.transaction_type)
    print("transaction_amount:", reconciliation.transaction_amount)
    print("reconciliation_status:", reconciliation.reconciliation_status)
    print("internal_reference:", reconciliation.internal_reference)
    print("external_reference:", reconciliation.external_reference)
    print("transaction_date:", reconciliation.transaction_date)
    print("reconciled_at:", reconciliation.reconciled_at)

finally:
    db.close()