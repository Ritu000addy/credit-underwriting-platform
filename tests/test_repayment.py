from datetime import datetime
from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.services.repayment_service import repayment_service


db = SessionLocal()

try:
    repayment = repayment_service.create_repayment(
        db=db,
        repayment_id="DEV-ORCH-REPAYMENT-PAY-001",
        application_id="PERSIST-TEST-001",
        repayment_amount=Decimal("13327.32"),
        status="SUCCESS",
        repayment_schedule_id="DEV-ORCH-REPAYMENT-001",
        repayment_reference="REPAY-REF-001",
        payment_mode="NACH",
        payment_provider="DEV-PAYMENT-PROVIDER",
        principal_allocated=Decimal("11827.32"),
        interest_allocated=Decimal("1500.00"),
        paid_at=datetime(2026, 10, 25),
    )

    print("REPAYMENT CREATED")
    print("repayment_id:", repayment.repayment_id)
    print("application_id:", repayment.application_id)
    print("repayment_schedule_id:", repayment.repayment_schedule_id)
    print("repayment_amount:", repayment.repayment_amount)
    print("status:", repayment.status)
    print("repayment_reference:", repayment.repayment_reference)
    print("payment_mode:", repayment.payment_mode)
    print("payment_provider:", repayment.payment_provider)
    print("principal_allocated:", repayment.principal_allocated)
    print("interest_allocated:", repayment.interest_allocated)
    print("paid_at:", repayment.paid_at)

finally:
    db.close()