from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class CreditPolicyRule(Base):
    __tablename__ = "credit_policy_rules"

    rule_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    rule_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    rule_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    rule_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    rule_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    threshold_value: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )

    threshold_text: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    action: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    policy_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    effective_from: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )