from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class InternalHistory(Base):
    __tablename__ = "internal_history"

    __table_args__ = (
        Index(
            "ix_internal_history_application_analyzed",
            "application_id",
            "analyzed_at",
        ),
        CheckConstraint(
            "previous_loans_count IS NULL OR previous_loans_count >= 0",
            name="ck_internal_history_previous_loans_count_non_negative",
        ),
        CheckConstraint(
            "active_loans_count IS NULL OR active_loans_count >= 0",
            name="ck_internal_history_active_loans_count_non_negative",
        ),
        CheckConstraint(
            "closed_loans_count IS NULL OR closed_loans_count >= 0",
            name="ck_internal_history_closed_loans_count_non_negative",
        ),
        CheckConstraint(
            "total_previous_exposure IS NULL OR total_previous_exposure >= 0",
            name="ck_internal_history_total_previous_exposure_non_negative",
        ),
        CheckConstraint(
            "total_outstanding_amount IS NULL OR total_outstanding_amount >= 0",
            name="ck_internal_history_total_outstanding_amount_non_negative",
        ),
        CheckConstraint(
            "dpd_count IS NULL OR dpd_count >= 0",
            name="ck_internal_history_dpd_count_non_negative",
        ),
        CheckConstraint(
            "max_dpd IS NULL OR max_dpd >= 0",
            name="ck_internal_history_max_dpd_non_negative",
        ),
        CheckConstraint(
            "overdue_amount IS NULL OR overdue_amount >= 0",
            name="ck_internal_history_overdue_amount_non_negative",
        ),
        CheckConstraint(
            "write_off_count IS NULL OR write_off_count >= 0",
            name="ck_internal_history_write_off_count_non_negative",
        ),
        CheckConstraint(
            "settlement_count IS NULL OR settlement_count >= 0",
            name="ck_internal_history_settlement_count_non_negative",
        ),
    )

    internal_history_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    previous_loans_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    active_loans_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    closed_loans_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_previous_exposure: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    total_outstanding_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    repayment_history: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    dpd_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    max_dpd: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    overdue_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    write_off_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    settlement_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    last_loan_date: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    analysis_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )