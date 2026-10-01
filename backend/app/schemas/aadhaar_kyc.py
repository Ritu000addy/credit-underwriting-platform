from pydantic import BaseModel


class AadhaarKYCResponse(BaseModel):
    status: str
    transaction_id: str | None = None
    kyc_status: str
    session_id: str | None = None

    name: str | None = None
    dob: str | None = None
    gender: str | None = None
    address: str | None = None

    care_of: str | None = None
    house: str | None = None
    street: str | None = None
    landmark: str | None = None
    locality: str | None = None
    district: str | None = None
    sub_district: str | None = None
    state: str | None = None
    pincode: str | None = None
    post_office: str | None = None

    has_photo: bool | None = None
    photo: str | None = None

    masked_aadhaar: str | None = None

    error_code: dict | None = None
    error_message: str | None = None