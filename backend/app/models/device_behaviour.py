from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class DeviceBehaviour(Base):
    __tablename__ = "device_behaviour"

    device_behaviour_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    device_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    device_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    operating_system: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    app_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    device_age_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    login_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    session_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    failed_login_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    application_velocity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    device_velocity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    ip_velocity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    behavioural_risk_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    fraud_indicator: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    analysis_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )