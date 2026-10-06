from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PolicyVersionCreate(BaseModel):
    policy_version: str = Field(min_length=1, max_length=100)
    effective_from: datetime
    effective_to: datetime | None = None
    policy_reference: str | None = Field(default=None, max_length=500)
    governance_notes: str | None = Field(default=None, max_length=2000)

    @field_validator("policy_version", mode="before")
    @classmethod
    def normalize_policy_version(cls, value):
        if value is None:
            return value
        value = str(value).strip()
        if not value:
            raise ValueError("POLICY_VERSION_REQUIRED")
        return value

    @field_validator("effective_to")
    @classmethod
    def validate_effective_dates(cls, value, info):
        effective_from = info.data.get("effective_from")

        if (
            value is not None
            and effective_from is not None
            and value < effective_from
        ):
            raise ValueError(
                "POLICY_EFFECTIVE_TO_BEFORE_EFFECTIVE_FROM"
            )

        return value


class PolicyVersionAction(BaseModel):
    policy_version: str = Field(min_length=1, max_length=100)
    actor_id: str = Field(min_length=1, max_length=200)

    @field_validator("policy_version", "actor_id", mode="before")
    @classmethod
    def normalize_values(cls, value):
        if value is None:
            return value
        value = str(value).strip()
        if not value:
            raise ValueError("FIELD_REQUIRED")
        return value


class PolicyVersionRollback(BaseModel):
    actor_id: str = Field(min_length=1, max_length=200)
    target_policy_version: str = Field(min_length=1, max_length=100)

    @field_validator("actor_id", "target_policy_version", mode="before")
    @classmethod
    def normalize_values(cls, value):
        if value is None:
            return value
        value = str(value).strip()
        if not value:
            raise ValueError("FIELD_REQUIRED")
        return value


class PolicyVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    policy_version_id: str
    policy_version: str
    effective_from: datetime
    effective_to: datetime | None = None
    status: str
    policy_reference: str | None = None
    governance_notes: str | None = None
    created_at: datetime
    updated_at: datetime