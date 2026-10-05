from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Disbursement(Base):
    __tablename__ = "disbursements"

    __table_args__ = (
        Index(
            "ix_disbursements_application_created",
            "application_id",
            "created_at",
        ),
        Index(
            "ix_disbursements_status_created",
            "status",
            "created_at",
        ),
        CheckConstraint(
            "disbursement_amount > 0",
            name="ck_disbursements_amount_positive",
        ),
        CheckConstraint(
            "retry_attempts >= 0",
            name="ck_disbursements_retry_attempts_non_negative",
        ),
        CheckConstraint(
            "status IN ('CREATED', 'INITIATED', 'PROCESSING', 'PROCESSED', 'FAILED')",
            name="ck_disbursements_status",
        ),
    )

    disbursement_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    sanction_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("sanctions.sanction_id"),
        nullable=True,
    )

    disbursement_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    beneficiary_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    bank_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    payment_provider: Mapped[str | None] = mapped_column(
        String(100),
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

    retry_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    initiated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
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