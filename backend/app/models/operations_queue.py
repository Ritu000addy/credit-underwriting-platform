from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class OperationsQueue(Base):
    __tablename__ = "operations_queue"

    queue_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    reconciliation_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    disbursement_id: Mapped[str | None] = mapped_column(
        String(50),
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