from datetime import datetime

from pydantic import BaseModel


class BeneficiaryCreate(BaseModel):
    application_id: str
    account_holder_name: str
    account_number_reference: str
    ifsc_code: str
    bank_name: str


class BeneficiaryResponse(BaseModel):
    beneficiary_id: str
    application_id: str
    account_holder_name: str | None = None
    account_number_reference: str | None = None
    ifsc_code: str | None = None
    bank_name: str | None = None
    validation_status: str
    validation_reference: str | None = None
    failure_reason: str | None = None
    validated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime