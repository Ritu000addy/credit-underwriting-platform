from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Collection(Base):
    __tablename__ = "collections"

    __table_args__ = (
        Index(
            "ix_collections_application_created",
            "application_id",
            "created_at",
        ),
        Index(
            "ix_collections_schedule_created",
            "repayment_schedule_id",
            "created_at",
        ),
        UniqueConstraint(
            "collection_reference",
            name="uq_collections_collection_reference",
        ),
        CheckConstraint(
            "due_amount >= 0",
            name="ck_collections_due_amount_non_negative",
        ),
        CheckConstraint(
            "collected_amount >= 0",
            name="ck_collections_collected_amount_non_negative",
        ),
        CheckConstraint(
            "outstanding_amount >= 0",
            name="ck_collections_outstanding_amount_non_negative",
        ),
        CheckConstraint(
            "days_past_due >= 0",
            name="ck_collections_days_past_due_non_negative",
        ),
        CheckConstraint(
            "collected_amount <= due_amount",
            name="ck_collections_collected_amount_not_over_due",
        ),
        CheckConstraint(
            "outstanding_amount <= due_amount",
            name="ck_collections_outstanding_amount_not_over_due",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'PARTIAL', 'COLLECTED')",
            name="ck_collections_status",
        ),
        CheckConstraint(
            "status <> 'PENDING' "
            "OR (collected_amount = 0 AND outstanding_amount = due_amount)",
            name="ck_collections_pending_status_consistency",
        ),
        CheckConstraint(
            "status <> 'COLLECTED' "
            "OR outstanding_amount = 0",
            name="ck_collections_collected_status_consistency",
        ),
        CheckConstraint(
            "status <> 'PARTIAL' "
            "OR outstanding_amount > 0",
            name="ck_collections_partial_status_consistency",
        ),
    )

    collection_id: Mapped[str] = mapped_column(
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

    collection_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    due_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    collected_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    outstanding_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    days_past_due: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    collection_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    collection_channel: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    collected_at: Mapped[datetime | None] = mapped_column(
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