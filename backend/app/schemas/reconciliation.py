from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ReconciliationCreateRequest(BaseModel):
    application_id: str | None = None
    disbursement_id: str | None = None

    transaction_type: str

    internal_reference: str | None = None
    external_reference: str | None = None

    transaction_amount: Decimal
    transaction_date: datetime | None = None

    reconciliation_status: str

    mismatch_reason: str | None = None
    reconciled_at: datetime | None = None


class ReconciliationResponse(BaseModel):
    reconciliation_id: str
    application_id: str | None = None
    disbursement_id: str | None = None

    transaction_type: str

    internal_reference: str | None = None
    external_reference: str | None = None

    transaction_amount: Decimal
    transaction_date: datetime | None = None

    reconciliation_status: str

    mismatch_reason: str | None = None
    reconciled_at: datetime | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}