from decimal import Decimal
from datetime import datetime
from pydantic import ConfigDict
from pydantic import BaseModel


class BankAnalysisCreate(BaseModel):
    application_id: str

    monthly_credits: Decimal | None = None
    monthly_debits: Decimal | None = None
    average_balance: Decimal | None = None
    existing_emi: Decimal | None = None

    bounce_count: int | None = None
    transactions_count: int | None = None

    income_trend: str | None = None
    analysis_reference: str | None = None

class BankAnalysisResponse(BankAnalysisCreate):
    model_config = ConfigDict(from_attributes=True)

    bank_analysis_id: str
    analyzed_at: datetime