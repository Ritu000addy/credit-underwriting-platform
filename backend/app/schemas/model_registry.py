from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelRegistryCreate(BaseModel):
    model_registry_id: str = Field(min_length=1, max_length=50)
    model_name: str = Field(min_length=1, max_length=100)
    model_version: str = Field(min_length=1, max_length=100)
    deployment_status: str = Field(min_length=1, max_length=30)

    model_type: str | None = Field(default=None, max_length=100)
    training_data_version: str | None = Field(default=None, max_length=100)
    training_date: datetime | None = None
    roc_auc: Decimal | None = None
    model_metrics: str | None = None
    environment: str | None = Field(default=None, max_length=50)
    model_reference: str | None = Field(default=None, max_length=500)
    governance_notes: str | None = None

    @field_validator(
        "model_registry_id",
        "model_name",
        "model_version",
        "deployment_status",
    )
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("MODEL_REGISTRY_FIELD_REQUIRED")

        return value


class ModelValidationStart(BaseModel):
    model_name: str = Field(min_length=1, max_length=100)
    model_version: str = Field(min_length=1, max_length=100)


class ModelValidationComplete(BaseModel):
    model_name: str = Field(min_length=1, max_length=100)
    model_version: str = Field(min_length=1, max_length=100)
    passed: bool
    validated_by: str = Field(min_length=1, max_length=100)
    validation_notes: str | None = None


class ModelApprovalRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=100)
    model_version: str = Field(min_length=1, max_length=100)
    approved_by: str = Field(min_length=1, max_length=100)


class ModelVersionRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=100)
    model_version: str = Field(min_length=1, max_length=100)


class ModelRollbackRequest(BaseModel):
    model_name: str = Field(min_length=1, max_length=100)
    current_version: str = Field(min_length=1, max_length=100)
    rollback_version: str = Field(min_length=1, max_length=100)


class ModelRegistryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_registry_id: str
    model_name: str
    model_version: str
    model_type: str | None = None
    training_data_version: str | None = None
    training_date: datetime | None = None
    roc_auc: Decimal | None = None
    model_metrics: str | None = None
    deployment_status: str

    lifecycle_status: str
    validation_status: str
    validation_date: datetime | None = None
    validated_by: str | None = None
    validation_notes: str | None = None
    approval_date: datetime | None = None
    approved_by: str | None = None
    rollback_of_version: str | None = None
    governance_notes: str | None = None

    environment: str | None = None
    model_reference: str | None = None

    created_at: datetime
    updated_at: datetime