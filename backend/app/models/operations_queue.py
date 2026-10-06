from datetime import datetime

from sqlalchemy import DateTime, String, Text, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class OperationsQueue(Base):
    __tablename__ = "operations_queue"

    __table_args__ = (
        CheckConstraint(
            "queue_status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')",
            name="ck_operations_queue_status",
        ),
        CheckConstraint(
            "queue_type IN ('RECONCILIATION_MISMATCH')",
            name="ck_operations_queue_type",
        ),
    )

    queue_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    reconciliation_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("reconciliation.reconciliation_id"),
        nullable=True,
    )

    disbursement_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("disbursements.disbursement_id"),
        nullable=True,
    )

    queue_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    queue_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
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