from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Reconciliation(Base):
    __tablename__ = "reconciliation"

    __table_args__ = (
        Index(
            "ix_reconciliation_disbursement_created",
            "disbursement_id",
            "created_at",
        ),
        CheckConstraint(
            "transaction_amount >= 0",
            name="ck_reconciliation_transaction_amount_non_negative",
        ),
    )

    reconciliation_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=True,
    )

    disbursement_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("disbursements.disbursement_id"),
        nullable=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    internal_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    external_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    transaction_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    transaction_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    reconciliation_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    mismatch_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reconciled_at: Mapped[datetime | None] = mapped_column(
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