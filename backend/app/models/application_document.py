from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base

class ApplicationDocument(Base):
    __tablename__ = "application_documents"

    document_id: Mapped[str] = mapped_column(
        String(50),
        primary_key = True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable = False,
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable = False,
    )

    verification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    document_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    document_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default = datetime.utcnow,
        onupdate = datetime.utcnow,
        nullable= False,
    )