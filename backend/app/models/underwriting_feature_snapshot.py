from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class UnderwritingFeatureSnapshot(Base):
    __tablename__ = "underwriting_feature_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "decision_id",
            name="uq_underwriting_feature_snapshots_decision_id",
        ),
        Index(
            "ix_underwriting_feature_snapshots_application_created",
            "application_id",
            "created_at",
        ),
    )

    feature_snapshot_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    decision_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("credit_decisions.decision_id"),
        nullable=False,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    feature_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
    )

    features: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )