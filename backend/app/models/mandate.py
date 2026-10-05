from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Mandate(Base):
    __tablename__ = "mandates"

    __table_args__ = (
    UniqueConstraint(
        "application_id",
        name="uq_mandates_application",
    ),
    Index(
        "ix_mandates_status_created",
        "status",
        "created_at",
    ),
    CheckConstraint(
        "status IN ('INITIATED', 'COMPLETED', 'FAILED')",
        name="ck_mandates_status",
    ),
)

    mandate_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    mandate_reference: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    mandate_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    provider: Mapped[str | None] = mapped_column(
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

    initiated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
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