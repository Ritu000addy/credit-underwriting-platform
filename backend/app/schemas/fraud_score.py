from decimal import Decimal

from pydantic import BaseModel, Field


class FraudScoreResult(BaseModel):
    fraud_score: Decimal | None = None
    risk_level: str | None = None
    confidence: Decimal | None = None
    reason_codes: list[str] = Field(default_factory=list)