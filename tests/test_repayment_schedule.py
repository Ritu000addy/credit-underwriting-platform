from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from backend.app.database import SessionLocal
from backend.app.services.repayment_schedule_service import (
    repayment_schedule_service,
)
from backend.app.models.repayment_schedule import RepaymentSchedule


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10].upper()}"


def test_repayment_schedule_persistence():
    db = SessionLocal()

    try:
        last_installment = (
            db.query(RepaymentSchedule.installment_number)
            .filter(
                RepaymentSchedule.disbursement_id
                == "DEV-ORCH-DISBURSEMENT-001"
            )
            .order_by(
                RepaymentSchedule.installment_number.desc()
            )
            .first()
        )

        installment_number = (
            (last_installment[0] + 1)
            if last_installment is not None
            else 1
        )

        repayment_schedule_id = unique("DEV-REPAYMENT")

        installment = repayment_schedule_service.create_installment(
            db=db,
            repayment_schedule_id=repayment_schedule_id,
            application_id="PERSIST-TEST-001",
            disbursement_id="DEV-ORCH-DISBURSEMENT-001",
            installment_number=installment_number,
            due_date=datetime(2026, 11, 25),
            principal_due=Decimal("12000.00"),
            interest_due=Decimal("1327.32"),
            total_due=Decimal("13327.32"),
            outstanding_principal=Decimal("126172.68"),
            status="PENDING",
        )

        assert (
            installment.repayment_schedule_id
            == repayment_schedule_id
        )
        assert installment.application_id == "PERSIST-TEST-001"
        assert (
            installment.disbursement_id
            == "DEV-ORCH-DISBURSEMENT-001"
        )
        assert installment.installment_number == installment_number
        assert installment.due_date == datetime(2026, 11, 25)
        assert installment.principal_due == Decimal("12000.00")
        assert installment.interest_due == Decimal("1327.32")
        assert installment.total_due == Decimal("13327.32")
        assert installment.outstanding_principal == Decimal(
            "126172.68"
        )
        assert installment.status == "PENDING"

    finally:
        db.close()