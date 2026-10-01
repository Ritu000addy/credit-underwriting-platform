from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class ModelRegistry(Base):
    __tablename__ = "model_registry"

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