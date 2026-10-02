import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.repayment import Repayment
from backend.app.models.repayment_schedule import RepaymentSchedule

from backend.app.services.audit_log_service import audit_log_service

class RepaymentService:

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
        paid_at: datetime | None = None,
    ) -> Repayment:

        repayment = Repayment(
            repayment_id=repayment_id,
            application_id=application_id,
            repayment_schedule_id=repayment_schedule_id,
            repayment_reference=repayment_reference,
            repayment_amount=repayment_amount,
            payment_mode=payment_mode,
            payment_provider=payment_provider,
            principal_allocated=principal_allocated,
            interest_allocated=interest_allocated,
            status=status,
            failure_reason=failure_reason,
            paid_at=paid_at,
        )

        db.add(repayment)
        db.commit()
        db.refresh(repayment)

        return repayment

    def record_repayment(
        self,
        db: Session,
        repayment_id: str,
        application_id: str,
        repayment_schedule_id: str,
        repayment_amount: Decimal,
        repayment_reference: str | None = None,
        payment_mode: str | None = None,
        payment_provider: str | None = None,
    ) -> Repayment:

        schedule = (
            db.query(RepaymentSchedule)
            .filter(
                RepaymentSchedule.repayment_schedule_id
                == repayment_schedule_id
            )
            .first()
        )

        if schedule is None:
            raise ValueError("REPAYMENT_SCHEDULE_NOT_FOUND")

        if schedule.application_id != application_id:
            raise ValueError("APPLICATION_MISMATCH")

        if schedule.status == "PAID":
            raise ValueError("INSTALLMENT_ALREADY_PAID")

        previous_schedule_status = schedule.status

        if repayment_amount <= Decimal("0.00"):
            raise ValueError("INVALID_REPAYMENT_AMOUNT")

        existing_repayments = (
            db.query(Repayment)
                .filter(
                    Repayment.repayment_schedule_id == repayment_schedule_id,
                    Repayment.status == "SUCCESS",
                )
                .all()
        )

        total_repaid = sum(
            (
                repayment.repayment_amount
                for repayment in existing_repayments
            ),
            Decimal("0.00"),
        )

        remaining_amount = schedule.total_due - total_repaid

        if repayment_amount > remaining_amount:
            raise ValueError("REPAYMENT_AMOUNT_EXCEEDS_OUTSTANDING")

        is_fully_paid = repayment_amount == remaining_amount

        payment_ratio = repayment_amount / schedule.total_due

        principal_allocated = (
            schedule.principal_due * payment_ratio
        ).quantize(Decimal("0.01"))

        interest_allocated = (
            repayment_amount - principal_allocated
        ).quantize(Decimal("0.01"))

        paid_at = datetime.utcnow()

        repayment = Repayment(
            repayment_id=repayment_id,
            application_id=application_id,
            repayment_schedule_id=repayment_schedule_id,
            repayment_reference=repayment_reference,
            repayment_amount=repayment_amount,
            payment_mode=payment_mode,
            payment_provider=payment_provider,
            principal_allocated=principal_allocated,
            interest_allocated=interest_allocated,
            status="SUCCESS",
            paid_at=paid_at,
        )

        if is_fully_paid:
            schedule.status = "PAID"
            schedule.paid_at = paid_at

        db.add(repayment)

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=application_id,
            actor_type="SYSTEM",
            action="REPAYMENT_RECORDED",
            entity_type="REPAYMENT",
            entity_reference=repayment.repayment_id,
            description=(
                f"Repayment of {repayment_amount} recorded successfully."
            ),
            previous_state=previous_schedule_status,
            new_state=schedule.status,
            request_reference=repayment_reference,
        )
        db.commit()
        db.refresh(repayment)

        return repayment

repayment_service = RepaymentService()