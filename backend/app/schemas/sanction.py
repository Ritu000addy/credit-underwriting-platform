from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SanctionCreate(BaseModel):
    application_id: str
    sanctioned_amount: Decimal
    sanctioned_tenure: int
    sanctioned_emi: Decimal | None = None
    interest_rate: Decimal | None = None
    approval_authority: str | None = None
    terms_and_conditions: str | None = None
    expires_at: datetime | None = None


class SanctionResponse(BaseModel):
    sanction_id: str
    application_id: str
    sanctioned_amount: Decimal
    sanctioned_tenure: int
    sanctioned_emi: Decimal | None = None
    interest_rate: Decimal | None = None
    sanction_status: str
    approval_authority: str | None = None
    terms_and_conditions: str | None = None
    sanctioned_at: datetime
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime