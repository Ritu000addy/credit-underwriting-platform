from decimal import Decimal

from pydantic import BaseModel, Field

class FraudRiskResult(BaseModel):
    fraud_score: Decimal | None = None
    risk_level: str | None = None
    confidence: Decimal | None = None
    reason_codes: list[str] = Field(default_factory=list)
    model_version: str | None = None