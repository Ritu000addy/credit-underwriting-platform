from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base

class BankAnalysis(Base):
    __tablename__ = "bank_analysis"

    __table_args__ = (
        Index(
            "ix_bank_analysis_application_analyzed",
            "application_id",
            "analyzed_at",
        ),
        CheckConstraint(
            "monthly_credits IS NULL OR monthly_credits >= 0",
            name="ck_bank_analysis_monthly_credits_non_negative",
        ),
        CheckConstraint(
            "monthly_debits IS NULL OR monthly_debits >= 0",
            name="ck_bank_analysis_monthly_debits_non_negative",
        ),
        CheckConstraint(
            "existing_emi IS NULL OR existing_emi >= 0",
            name="ck_bank_analysis_existing_emi_non_negative",
        ),
        CheckConstraint(
            "bounce_count IS NULL OR bounce_count >= 0",
            name="ck_bank_analysis_bounce_count_non_negative",
        ),
        CheckConstraint(
            "transactions_count IS NULL OR transactions_count >= 0",
            name="ck_bank_analysis_transactions_count_non_negative",
        ),
    )

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