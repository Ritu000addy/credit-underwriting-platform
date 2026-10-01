from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class InternalHistory(Base):
    __tablename__ = "internal_history"

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