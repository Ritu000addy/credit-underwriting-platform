from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class DecisionTrace(Base):
    __tablename__ = "decision_traces"

    __table_args__ = (
        UniqueConstraint(
            "decision_id",
            name="uq_decision_traces_decision_id",
        ),
        Index(
            "ix_decision_traces_application_created",
            "application_id",
            "created_at",
        ),
    )

    trace_id: Mapped[str] = mapped_column(
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

    feature_snapshot_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey(
            "underwriting_feature_snapshots.feature_snapshot_id"
        ),
        nullable=True,
    )

    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    policy_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    effective_from: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    effective_to: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    model_outputs: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    policy_evaluation: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    reason_codes: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    decision_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )