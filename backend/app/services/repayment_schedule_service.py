import calendar
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select

from sqlalchemy.orm import Session

from backend.app.models.repayment_schedule import RepaymentSchedule
from backend.app.models.repayment import Repayment
from backend.app.models.disbursement import Disbursement

class RepaymentScheduleService:

    def create_installment(
        self,
        db: Session,
        repayment_schedule_id: str,
        application_id: str,
        disbursement_id: str,
        installment_number: int,
        due_date: datetime,
        principal_due: Decimal,
        interest_due: Decimal,
        total_due: Decimal,
        outstanding_principal: Decimal,
        status: str,
        paid_at: datetime | None = None,
    ) -> RepaymentSchedule:

        if status != "PENDING":
            raise ValueError(
                "INVALID_INITIAL_REPAYMENT_SCHEDULE_STATUS"
            )

        disbursement = db.get(
            Disbursement,
            disbursement_id,
        )

        if disbursement is None:
            raise ValueError(
                "DISBURSEMENT_NOT_FOUND"
            )

        if disbursement.application_id != application_id:
            raise ValueError(
                "DISBURSEMENT_APPLICATION_MISMATCH"
            )

        if disbursement.status != "PROCESSED":
            raise ValueError(
                "DISBURSEMENT_NOT_PROCESSED"
            )

        if paid_at is not None:
            raise ValueError(
                "PENDING_INSTALLMENT_CANNOT_HAVE_PAID_AT"
            )

        installment = RepaymentSchedule(
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

        db.add(installment)
        db.commit()
        db.refresh(installment)

        return installment

    def generate_schedule(
        self,
        db: Session,
        application_id: str,
        disbursement_id: str,
        principal: Decimal,
        annual_interest_rate: Decimal,
        tenure_months: int,
        first_due_date: datetime,
    ) -> list[RepaymentSchedule]:

        disbursement = (
            db.query(Disbursement)
            .filter(
                Disbursement.disbursement_id == disbursement_id
            )
            .with_for_update()
            .first()
        )

        if disbursement is None:
            raise ValueError(
                "DISBURSEMENT_NOT_FOUND"
            )

        if disbursement.application_id != application_id:
            raise ValueError(
                "DISBURSEMENT_APPLICATION_MISMATCH"
            )

        if disbursement.status != "PROCESSED":
            raise ValueError(
                "DISBURSEMENT_NOT_PROCESSED"
            )

        if principal <= Decimal("0.00"):
            raise ValueError(
                "INVALID_SCHEDULE_PRINCIPAL"
            )

        if tenure_months <= 0:
            raise ValueError(
                "INVALID_SCHEDULE_TENURE"
            )

        existing_schedule = (
            db.query(RepaymentSchedule)
            .filter(
                RepaymentSchedule.disbursement_id == disbursement_id
            )
            .order_by(
                RepaymentSchedule.installment_number
            )
            .all()
        )

        if existing_schedule:
            return existing_schedule

        monthly_rate = annual_interest_rate / Decimal("12") / Decimal("100")

        if monthly_rate == 0:
            emi = principal / Decimal(tenure_months)
        else:
            emi = (
                principal
                * monthly_rate
                * (Decimal("1") + monthly_rate) ** tenure_months
                / (
                    (Decimal("1") + monthly_rate) ** tenure_months
                    - Decimal("1")
                )
            )

        emi = emi.quantize(Decimal("0.01"))

        outstanding_principal = principal
        installments = []

        for installment_number in range(1, tenure_months + 1):

            interest_due = (
                outstanding_principal * monthly_rate
            ).quantize(Decimal("0.01"))

            if installment_number == tenure_months:
                principal_due = outstanding_principal
                total_due = (
                    principal_due + interest_due
                ).quantize(Decimal("0.01"))
            else:
                principal_due = (
                    emi - interest_due
                ).quantize(Decimal("0.01"))

                total_due = (
                    principal_due + interest_due
                ).quantize(Decimal("0.01"))

            outstanding_principal = (
                outstanding_principal - principal_due
            ).quantize(Decimal("0.01"))

            if outstanding_principal < Decimal("0.00"):
                outstanding_principal = Decimal("0.00")

            month = first_due_date.month - 1 + (installment_number - 1)
            year = first_due_date.year + month // 12
            month = month % 12 + 1

            last_day_of_month = calendar.monthrange(year, month)[1]

            due_day = min(
                first_due_date.day,
                last_day_of_month,
            )

            due_date = first_due_date.replace(
                year=year,
                month=month,
                day=due_day,
            )

            installment = RepaymentSchedule(
                repayment_schedule_id=(
                    f"RS-{disbursement_id}-{installment_number:03d}"
                ),
                application_id=application_id,
                disbursement_id=disbursement_id,
                installment_number=installment_number,
                due_date=due_date,
                principal_due=principal_due,
                interest_due=interest_due,
                total_due=total_due,
                outstanding_principal=outstanding_principal,
                status="PENDING",
            )

            db.add(installment)
            installments.append(installment)

        db.commit()

        for installment in installments:
            db.refresh(installment)

        return installments

    def get_schedule_by_application(
        self,
        db: Session,
        application_id: str,
    ) -> list[RepaymentSchedule]:

        return (
            db.query(RepaymentSchedule)
            .filter(
                RepaymentSchedule.application_id == application_id
            )
            .order_by(
                RepaymentSchedule.installment_number
            )
            .all()
        )

    def get_schedule_by_disbursement(
        self,
        db: Session,
        application_id: str,
        disbursement_id: str,
    ) -> list[RepaymentSchedule]:

        return (
            db.query(RepaymentSchedule)
            .filter(
                RepaymentSchedule.application_id == application_id,
                RepaymentSchedule.disbursement_id == disbursement_id,
            )
            .order_by(
                RepaymentSchedule.installment_number
            )
            .all()
        )

    def get_repayment_summary(
        self,
        db: Session,
        application_id: str,
        disbursement_id: str,
    ) -> dict:

        schedule = self.get_schedule_by_disbursement(
            db=db,
            application_id=application_id,
            disbursement_id=disbursement_id,
        )

        total_installments = len(schedule)

        paid_installments = sum(
            1 
            for installment in schedule
            if installment.status == "PAID"
        )

        pending_installments = sum(
            1
            for installment in schedule
            if installment.status == "PENDING"
        )

        total_payable = sum(
            (installment.total_due for installment in schedule),
            Decimal("0.00"),
        )

        repayment_rows = (
            db.query(Repayment)
            .filter(
                Repayment.application_id == application_id,
                Repayment.status == "SUCCESS",
                Repayment.repayment_schedule_id.in_(
                    [
                        installment.repayment_schedule_id
                        for installment in schedule
                    ]
                ),
            )
            .all()
            if schedule
            else []
        )

        total_paid = sum(
            (
                repayment.repayment_amount
                for repayment in repayment_rows
            ),
            Decimal("0.00"),
        )

        total_outstanding = (
            total_payable - total_paid
        ).quantize(Decimal("0.01"))

        if total_outstanding < Decimal("0.00"):
            total_outstanding = Decimal("0.00")

        pending_schedule = [
            installment
            for installment in schedule
            if installment.status == "PENDING"
        ]

        next_pending_installment = None
        next_due_date = None
        next_due_amount = None

        if pending_schedule:
            next_installment = pending_schedule[0]

            next_pending_installment = (
                next_installment.installment_number
            )

            next_due_date = next_installment.due_date

            installment_paid = sum(
                (
                    repayment.repayment_amount
                    for repayment in repayment_rows
                    if repayment.repayment_schedule_id
                    == next_installment.repayment_schedule_id
                ),
                Decimal("0.00"),
            )
            next_due_amount = (
                next_installment.total_due - installment_paid
            ).quantize(Decimal("0.01"),
            )

            if next_due_amount < Decimal("0.00"):
                next_due_amount = Decimal("0.00")

        return {
            "application_id": application_id,
            "disbursement_id": disbursement_id,
            "total_installments": total_installments,
            "paid_installments": paid_installments,
            "pending_installments": pending_installments,
            "total_payable": total_payable,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "next_pending_installment": next_pending_installment,
            "next_due_date": next_due_date,
            "next_due_amount": next_due_amount,
        }

repayment_schedule_service = RepaymentScheduleService()