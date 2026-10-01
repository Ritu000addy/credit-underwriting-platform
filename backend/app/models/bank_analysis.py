from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base

class BankAnalysis(Base):
    __tablename__ = "bank_analysis"

    bank_analysis_id: Mapped[str] = mapped_column(
        String(50),
        primary_key = True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable = False,
    )

    monthly_credits: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    monthly_debits: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    average_balance: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    existing_emi: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    bounce_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    transactions_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    income_trend: Mapped[str | None] = mapped_column(
        String(30),
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