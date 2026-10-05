from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    __table_args__ = (
        Index(
            "ix_documents_application_created",
            "application_id",
            "created_at",
        ),
    )

    document_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    document_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    document_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    document_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    document_source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    verification_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    verification_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    extracted_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    analysis_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )