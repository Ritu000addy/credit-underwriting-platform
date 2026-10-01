from decimal import Decimal
from pydantic import BaseModel

class ApplicationCreate(BaseModel):
    application_id: str
    customer_id: str
    requested_amount: Decimal
    loan_tenure_months: int
    annual_interest_rate: Decimal | None = None