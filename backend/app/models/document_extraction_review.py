from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class DocumentExtractionReview(Base):
    __tablename__ = "document_extraction_reviews"

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'IN_REVIEW', 'APPROVED', 'REJECTED')",
            name="ck_document_extraction_reviews_status",
        ),
        UniqueConstraint(
            "analysis_reference",
            name="uq_document_extraction_reviews_analysis_reference",
        ),
        Index(
            "ix_document_extraction_reviews_application_status",
            "application_id",
            "status",
        ),
        Index(
            "ix_document_extraction_reviews_assignee_status",
            "assigned_reviewer_id",
            "status",
        ),
    )

    review_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    document_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("documents.document_id"),
        nullable=False,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    analysis_reference: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
    )

    # Immutable-at-review-time snapshot of the extraction result.
    extraction_snapshot: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    assigned_reviewer_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("auth_users.user_id"),
        nullable=True,
    )

    assigned_by_user_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("auth_users.user_id"),
        nullable=True,
    )

    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    reviewed_by_user_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("auth_users.user_id"),
        nullable=True,
    )

    accepted_fields: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    accepted_values: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    acknowledged_conflicts: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
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