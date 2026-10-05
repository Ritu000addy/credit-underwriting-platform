from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ManualReviewHistory(Base):
    __tablename__ = "manual_review_history"

    __table_args__ = (
        Index(
            "ix_manual_review_history_review_created",
            "review_id",
            "created_at",
        ),
        Index(
            "ix_manual_review_history_application_created",
            "application_id",
            "created_at",
        ),
    )

    history_id: Mapped[str] = mapped_column(
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

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    previous_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    new_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    actor_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    actor_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    reviewer_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    reviewer_decision: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )