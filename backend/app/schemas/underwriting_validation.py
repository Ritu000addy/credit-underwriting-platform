from pydantic import BaseModel, Field


class UnderwritingValidationResponse(BaseModel):
    application_id: str

    completeness_status: str = Field(
        description="Overall completeness status of underwriting input"
    )

    kyc_complete: bool
    bureau_available: bool
    bank_data_available: bool
    employment_data_available: bool
    internal_history_available: bool
    device_behaviour_available: bool
    documents_available: bool

    missing_data: list[str] = Field(default_factory=list)

    validation_errors: list[str] = Field(default_factory=list)