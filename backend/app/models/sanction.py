from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Sanction(Base):
    __tablename__ = "sanctions"

    __table_args__ = (
        UniqueConstraint(
            "application_id",
            name="uq_sanctions_application",
        ),
        CheckConstraint(
            "sanctioned_amount > 0",
            name="ck_sanctions_amount_positive",
        ),
        CheckConstraint(
            "sanctioned_tenure > 0",
            name="ck_sanctions_tenure_positive",
        ),
        CheckConstraint(
            "sanctioned_emi IS NULL OR sanctioned_emi >= 0",
            name="ck_sanctions_emi_non_negative",
        ),
        CheckConstraint(
            "interest_rate IS NULL OR interest_rate >= 0",
            name="ck_sanctions_interest_rate_non_negative",
        ),
    )

    sanction_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    sanctioned_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    sanctioned_tenure: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sanctioned_emi: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    interest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    sanction_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    approval_authority: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    terms_and_conditions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sanctioned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
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