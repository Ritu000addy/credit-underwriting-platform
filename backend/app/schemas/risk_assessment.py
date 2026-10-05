from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Any

class RiskAssessmentResult(BaseModel):
    status: str
    
    # Core Risk Outputs
    credit_score: int | None = None
    risk_grade: str | None = None
    probability_of_default: Decimal | None = None

    # Affordability / Repayment Assessment
    affordability_score: Decimal | None = None
    existing_obligation_ratio: Decimal | None = None
    repayment_propensity: Decimal | None = None

    # Fraud / Income Assessment
    fraud_score: Decimal | None = None
    fraud_risk_level: str | None = None
    fraud_confidence: Decimal | None = None
    fraud_reason_codes: list[str] = Field(default_factory=list)
    
    income_stability_score: Decimal | None = None
    income_trend: str | None = None

    # Loan Recommendation
    recommended_amount: Decimal | None = None
    recommended_tenure: int | None = None
    recommended_emi: Decimal | None = None

    # Affordability Indicator
    foir: Decimal | None = None

    # Risk Segmentation
    risk_segment: str | None = None

    # Model Confidence
    confidence: Decimal | None = None

    # Explainability
    reason_codes: list[str] = Field(default_factory=list)
    
    # Model Governance
    model_version: str | None = None
    model_features: dict[str, Any] | None = None