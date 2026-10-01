from decimal import Decimal

from pydantic import BaseModel

class CreditRiskModelOutput(BaseModel):
    probability_of_default: Decimal | None = None
    credit_score: int | None = None
    risk_grade: str | None = None
    confidence: Decimal | None = None
    model_version: str | None = None