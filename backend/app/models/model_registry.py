from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    __table_args__ = (
        CheckConstraint(
            "roc_auc IS NULL OR (roc_auc >= 0 AND roc_auc <= 1)",
            name="ck_model_registry_roc_auc_range",
        ),
        CheckConstraint(
            "lifecycle_status IN "
            "('REGISTERED', 'VALIDATION', 'APPROVED', 'ACTIVE', "
            "'INACTIVE', 'ROLLED_BACK', 'REJECTED')",
            name="ck_model_registry_lifecycle_status",
        ),
        CheckConstraint(
            "validation_status IN "
            "('NOT_VALIDATED', 'IN_PROGRESS', 'PASSED', 'FAILED')",
            name="ck_model_registry_validation_status",
        ),
    )

    model_registry_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    training_data_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    training_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    roc_auc: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 6),
        nullable=True,
    )

    model_metrics: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    deployment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    lifecycle_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="REGISTERED",
        server_default="REGISTERED",
    )

    validation_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="NOT_VALIDATED",
        server_default="NOT_VALIDATED",
    )

    validation_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    validated_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    validation_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    approval_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    rollback_of_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    governance_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    environment: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    model_reference: Mapped[str | None] = mapped_column(
        String(500),
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