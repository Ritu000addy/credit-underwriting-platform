from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ReviewException(Base):
    __tablename__ = "review_exceptions"

    __table_args__ = (
        Index(
            "ix_review_exceptions_application_status",
            "application_id",
            "status",
        ),
        Index(
            "ix_review_exceptions_review_created",
            "review_id",
            "created_at",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'IN_PROGRESS', 'WAITING_FOR_INFORMATION', 'RESOLVED', 'CLOSED')",
            name="ck_review_exceptions_status",
        ),
        CheckConstraint(
            "resolution_action IS NULL OR "
            "resolution_action IN "
            "('APPROVE', 'REJECT', 'REQUEST_INFORMATION')",
            name="ck_review_exceptions_resolution_action",
        ),
    )

    exception_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    review_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("manual_reviews.review_id"),
        nullable=False,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    exception_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OPEN",
    )

    assigned_to: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    requested_information: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolution_action: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    resolution_remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resolved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
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