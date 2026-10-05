from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class RepaymentSchedule(Base):
    __tablename__ = "repayment_schedules"

    __table_args__ = (
        Index(
            "ix_repayment_schedules_application_installment",
            "application_id",
            "installment_number",
        ),
        Index(
            "ix_repayment_schedules_disbursement_installment",
            "disbursement_id",
            "installment_number",
        ),
        UniqueConstraint(
            "disbursement_id",
            "installment_number",
            name="uq_repayment_schedules_disbursement_installment",
        ),
        CheckConstraint(
            "installment_number >= 1",
            name="ck_repayment_schedules_installment_number_positive",
        ),
        CheckConstraint(
            "principal_due >= 0",
            name="ck_repayment_schedules_principal_due_non_negative",
        ),
        CheckConstraint(
            "interest_due >= 0",
            name="ck_repayment_schedules_interest_due_non_negative",
        ),
        CheckConstraint(
            "total_due >= 0",
            name="ck_repayment_schedules_total_due_non_negative",
        ),
        CheckConstraint(
            "outstanding_principal >= 0",
            name="ck_repayment_schedules_outstanding_principal_non_negative",
        ),
        CheckConstraint(
            "total_due = principal_due + interest_due",
            name="ck_repayment_schedules_total_due_consistency",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'PAID')",
            name="ck_repayment_schedules_status",
        ),
        CheckConstraint(
            "status <> 'PAID' OR paid_at IS NOT NULL",
            name="ck_repayment_schedules_paid_at_required",
        ),
    )

    repayment_schedule_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    disbursement_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("disbursements.disbursement_id"),
        nullable=False,
    )

    installment_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    due_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    principal_due: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    interest_due: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    total_due: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    outstanding_principal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )