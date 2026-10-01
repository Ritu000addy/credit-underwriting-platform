from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.schemas.policy import PolicyRuleResult

class CreditDecisionOutput(BaseModel):
    application_id: str

    # Core Risk Outputs
    credit_score: int | None = None
    risk_grade: str | None = None
    probability_of_default: Decimal | None = None

    # AI/ML Risk Indicators
    affordability_score: Decimal | None = None
    repayment_propensity: Decimal | None = None
    fraud_score: Decimal | None = None
    fraud_risk_level: str | None = None
    fraud_confidence: Decimal | None = None
    fraud_reason_codes: list[str] = Field(default_factory=list)
    income_stability_score: Decimal | None = None
    income_trend: str | None = None
    risk_segment: str | None = None

    # Loan Recommendation
    recommended_amount: Decimal | None = None
    recommended_tenure: int | None = None
    recommended_emi: Decimal | None = None

    # Affordability
    foir: Decimal | None = None

    # Final Decision
    decision: Literal[
        "APPROVE",
        "REFER",
        "REJECT",
    ] = "REFER"

    confidence: Decimal | None = None

    # Explainability
    reason_codes: list[str] = Field(default_factory=list)
    
    # Policy Results
    policy_checks: list[PolicyRuleResult] = Field(default_factory=list)
    
    # Model Governance
    model_version: str | None = None
    policy_version: str | None = None