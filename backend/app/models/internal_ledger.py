from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class InternalLedger(Base):
    __tablename__ = "internal_ledger"

    __table_args__ = (
        Index(
            "ix_internal_ledger_application_date",
            "application_id",
            "transaction_date",
        ),
        Index(
            "ix_internal_ledger_disbursement_date",
            "disbursement_id",
            "transaction_date",
        ),
        UniqueConstraint(
            "disbursement_id",
            "transaction_type",
            name="uq_internal_ledger_disbursement_transaction_type",
        ),
        CheckConstraint(
            "transaction_amount >= 0",
            name="ck_internal_ledger_transaction_amount_non_negative",
        ),
    )

    ledger_id: Mapped[str] = mapped_column(
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

    transaction_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    transaction_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    ledger_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
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