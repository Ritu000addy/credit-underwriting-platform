from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Index, CheckConstraint, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ManualReview(Base):
    __tablename__ = "manual_reviews"

    __table_args__ = (
    Index(
        "ix_manual_reviews_application_status",
        "application_id",
        "review_status",
    ),
    Index(
        "ix_manual_reviews_reviewer_id",
        "reviewer_id",
    ),
    Index(
        "ix_manual_reviews_checker_id",
        "checker_id",
    ),

    CheckConstraint(
        "review_status IN "
        "('OPEN', 'IN_PROGRESS', 'PENDING_CHECKER', 'COMPLETED')",
        name="ck_manual_reviews_status",
    ),

    CheckConstraint(
        "reviewer_decision IS NULL "
        "OR reviewer_decision IN ('APPROVE', 'REJECT')",
        name="ck_manual_reviews_reviewer_decision",
    ),

    CheckConstraint(
        "checker_decision IS NULL "
        "OR checker_decision IN ('APPROVE', 'REJECT')",
        name="ck_manual_reviews_checker_decision",
    ),

    CheckConstraint(
        "review_status <> 'IN_PROGRESS' "
        "OR reviewer_id IS NOT NULL",
        name="ck_manual_reviews_in_progress_reviewer",
    ),

    CheckConstraint(
        "review_status <> 'PENDING_CHECKER' "
        "OR (reviewer_id IS NOT NULL AND reviewer_decision IS NOT NULL)",
        name="ck_manual_reviews_pending_checker",
    ),

    CheckConstraint(
        "review_status <> 'COMPLETED' "
        "OR maker_checker_required = false "
        "OR checker_decision IS NOT NULL",
        name="ck_manual_reviews_completed_checker_decision",
    ),

    CheckConstraint(
        "checker_id IS NULL OR checker_id <> reviewer_id",
        name="ck_manual_reviews_maker_checker_separation",
    ),
)

    review_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    review_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    review_reason: Mapped[str | None] = mapped_column(
        Text,
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

    reviewer_remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    checker_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    checker_decision: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    checker_remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    checker_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    maker_checker_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
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