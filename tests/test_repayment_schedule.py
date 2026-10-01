from datetime import datetime
from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.services.repayment_schedule_service import (
    repayment_schedule_service,
)


db = SessionLocal()

try:
    installment = repayment_schedule_service.create_installment(
        db=db,
        repayment_schedule_id="DEV-ORCH-REPAYMENT-001",
        application_id="PERSIST-TEST-001",
        disbursement_id="DEV-ORCH-DISBURSEMENT-001",
        installment_number=1,
        due_date=datetime(2026, 10, 25),
        principal_due=Decimal("11827.32"),
        interest_due=Decimal("1500.00"),
        total_due=Decimal("13327.32"),
        outstanding_principal=Decimal("138172.68"),
        status="PENDING",
    )

    print("REPAYMENT INSTALLMENT CREATED")
    print("repayment_schedule_id:", installment.repayment_schedule_id)
    print("application_id:", installment.application_id)
    print("disbursement_id:", installment.disbursement_id)
    print("installment_number:", installment.installment_number)
    print("due_date:", installment.due_date)
    print("principal_due:", installment.principal_due)
    print("interest_due:", installment.interest_due)
    print("total_due:", installment.total_due)
    print("outstanding_principal:", installment.outstanding_principal)
    print("status:", installment.status)

finally:
    db.close()