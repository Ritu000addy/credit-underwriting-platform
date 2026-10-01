from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Repayment(Base):
    __tablename__ = "repayments"

    repayment_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    repayment_schedule_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("repayment_schedules.repayment_schedule_id"),
        nullable=True,
    )

    repayment_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    repayment_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    payment_mode: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    payment_provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    principal_allocated: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    interest_allocated: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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