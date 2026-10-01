from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class Employment(Base):
    __tablename__ = "employment"

    employment_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    employment_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    employer_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    monthly_income: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    employment_vintage_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    business_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    business_vintage_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    gst_registered: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    udyam_registered: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    income_source: Mapped[str | None] = mapped_column(
        String(50),
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