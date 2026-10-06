from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    __table_args__ = (
        UniqueConstraint(
            "policy_version",
            name="uq_policy_versions_policy_version",
        ),
        CheckConstraint(
            "status IN "
            "('DRAFT', 'ACTIVE', 'INACTIVE', 'ROLLED_BACK', 'RETIRED')",
            name="ck_policy_versions_status",
        ),
        CheckConstraint(
            "effective_to IS NULL "
            "OR effective_to >= effective_from",
            name="ck_policy_versions_effective_dates",
        ),
    )

    policy_version_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    policy_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    effective_from: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    policy_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    governance_notes: Mapped[str | None] = mapped_column(
        Text,
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