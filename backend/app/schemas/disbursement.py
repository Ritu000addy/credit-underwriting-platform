from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class DisbursementCreate(BaseModel):
    application_id: str
    disbursement_amount: Decimal

    sanction_id: str | None = None

    beneficiary_reference: str | None = None
    payment_provider: str | None = None
    idempotency_key: str

class DisbursementUpdate(BaseModel):
    status: str

    bank_reference: str | None = None
    failure_reason: str | None = None
    processed_at: datetime | None = None


class DisbursementResponse(BaseModel):
    disbursement_id: str
    application_id: str

    sanction_id: str | None = None
    disbursement_amount: Decimal

    beneficiary_reference: str | None = None
    bank_reference: str | None = None
    payment_provider: str | None = None
    idempotency_key: str | None = None
    status: str
    failure_reason: str | None = None

    initiated_at: datetime
    processed_at: datetime | None = None

class DisbursementEligibilityRequest(BaseModel):
    application_id: str
    sanction_id: str
    disbursement_amount: Decimal
    beneficiary_reference: str | None = None


class DisbursementEligibilityResponse(BaseModel):
    eligible: bool
    application_id: str
    sanction_id: str
    disbursement_amount: Decimal
    reasons: list[str]

class BankDisbursementWebhook(BaseModel):
    disbursement_id: str
    bank_reference: str
    status: str
    bank_amount: Decimal | None = None
    failure_reason: str | None = None