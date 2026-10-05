from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class CreditDecision(Base):
    __tablename__ = "credit_decisions"

    __table_args__ = (
        Index(
            "ix_credit_decisions_application_created",
            "application_id",
            "created_at",
        ),
        CheckConstraint(
            "decision IN ('APPROVE', 'REFER', 'REJECT')",
            name="ck_credit_decisions_decision",
        ),
        CheckConstraint(
            "risk_grade IS NULL OR risk_grade IN ('A', 'B', 'C', 'D', 'E')",
            name="ck_credit_decisions_risk_grade",
        ),
        CheckConstraint(
            "probability_of_default IS NULL OR "
            "(probability_of_default >= 0 AND probability_of_default <= 1)",
            name="ck_credit_decisions_pd_range",
        ),
        CheckConstraint(
            "confidence IS NULL OR "
            "(confidence >= 0 AND confidence <= 1)",
            name="ck_credit_decisions_confidence_range",
        ),
        CheckConstraint(
            "foir IS NULL OR foir >= 0",
            name="ck_credit_decisions_foir_non_negative",
        ),
        CheckConstraint(
            "foir IS NULL OR foir <= 100",
            name="ck_credit_decisions_foir_max_100",
        ),
        CheckConstraint(
            "recommended_amount IS NULL OR recommended_amount >= 0",
            name="ck_credit_decisions_recommended_amount_non_negative",
        ),
        CheckConstraint(
            "recommended_emi IS NULL OR recommended_emi >= 0",
            name="ck_credit_decisions_recommended_emi_non_negative",
        ),
        CheckConstraint(
            "recommended_tenure IS NULL OR recommended_tenure >= 0",
            name="ck_credit_decisions_recommended_tenure_non_negative",
        ),
        CheckConstraint(
            "credit_score IS NULL OR credit_score >= 0",
            name="ck_credit_decisions_credit_score_non_negative",
        ),
        CheckConstraint(
            "affordability_score IS NULL OR "
            "(affordability_score >= 0 AND affordability_score <= 100)",
            name="ck_credit_decisions_affordability_score_range",
        ),
        CheckConstraint(
            "repayment_propensity IS NULL OR "
            "(repayment_propensity >= 0 AND repayment_propensity <= 100)",
            name="ck_credit_decisions_repayment_propensity_range",
        ),
        CheckConstraint(
            "fraud_score IS NULL OR "
            "(fraud_score >= 0 AND fraud_score <= 100)",
            name="ck_credit_decisions_fraud_score_range",
        ),
        CheckConstraint(
            "income_stability_score IS NULL OR "
            "(income_stability_score >= 0 AND income_stability_score <= 100)",
            name="ck_credit_decisions_income_stability_score_range",
        ),
        CheckConstraint(
            "risk_segment IS NULL OR "
            "risk_segment IN ('LOW_RISK', 'MEDIUM_RISK', 'HIGH_RISK')",
            name="ck_credit_decisions_risk_segment",
        ),
    )

    decision_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    application_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("loan_applications.application_id"),
        nullable=False,
    )

    credit_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    risk_grade: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    probability_of_default: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 6),
        nullable=True,
    )

    affordability_score: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    repayment_propensity: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    fraud_score: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    income_stability_score: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    recommended_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    recommended_tenure: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    recommended_emi: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    foir: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    risk_segment: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 6),
        nullable=True,
    )

    reason_codes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    policy_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=False,
    )

    effective_from: Mapped[str] = mapped_column(
        String(20), 
        nullable=False)

    effective_to: Mapped[str | None] = mapped_column(
        String(20), 
        nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )