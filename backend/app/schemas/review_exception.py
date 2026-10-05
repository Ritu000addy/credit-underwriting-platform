from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewExceptionCreate(BaseModel):
    review_id: str
    application_id: str
    exception_type: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    created_by: str | None = Field(default=None, max_length=100)


class ReviewExceptionAssign(BaseModel):
    assigned_to: str = Field(min_length=1, max_length=100)


class ReviewExceptionInformationRequest(BaseModel):
    requested_information: str = Field(min_length=1)
    actor_id: str = Field(min_length=1, max_length=100)


class ReviewExceptionResumeInformation(BaseModel):
    actor_id: str = Field(min_length=1, max_length=100)


class ReviewExceptionResolve(BaseModel):
    resolution_action: str
    resolution_remarks: str | None = None
    resolved_by: str = Field(min_length=1, max_length=100)

    @field_validator("resolution_action")
    @classmethod
    def validate_resolution_action(cls, value: str) -> str:
        value = value.strip().upper()

        if value not in {"APPROVE", "REJECT"}:
            raise ValueError(
                "RESOLUTION_ACTION_INVALID"
            )

        return value


class ReviewExceptionClose(BaseModel):
    actor_id: str = Field(min_length=1, max_length=100)


class ReviewExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exception_id: str
    review_id: str
    application_id: str
    exception_type: str
    description: str
    status: str
    assigned_to: str | None = None
    created_by: str | None = None
    requested_information: str | None = None
    resolution_action: str | None = None
    resolution_remarks: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime