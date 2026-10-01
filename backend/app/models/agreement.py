from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Agreement(Base):
    __tablename__ = "agreements"

    agreement_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    sanction_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("sanctions.sanction_id"),
        nullable=False,
    )

    agreement_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    agreement_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    esign_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    esign_provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    esign_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    document_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    initiated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    signed_at: Mapped[datetime | None] = mapped_column(
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