from datetime import date

from pydantic import BaseModel, ConfigDict


class CustomerCreate(BaseModel):
    customer_id: str
    kyc_status: str | None = None
    pan: str | None = None
    aadhaar_reference: str | None = None
    aadhaar_kyc_status: str | None = None
    dob: date | None = None
    address: str | None = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    customer_id: str
    kyc_status: str | None = None
    pan: str | None = None
    aadhaar_reference: str | None = None
    aadhaar_kyc_status: str | None = None
    dob: date | None = None
    address: str | None = None