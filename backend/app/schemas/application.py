from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ApplicationCreate(BaseModel):
    application_id: str
    customer_id: str
    requested_amount: Decimal
    loan_tenure_months: int
    annual_interest_rate: Decimal | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: str
    customer_id: str
    product: str | None = None
    requested_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime