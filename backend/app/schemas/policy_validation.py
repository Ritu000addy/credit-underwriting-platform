from pydantic import BaseModel, Field


class PolicyValidationResponse(BaseModel):
    application_id: str

    policy_status: str = Field(
        description="Overall deterministic policy validation status"
    )

    policy_checks: list[dict] = Field(
        default_factory=list,
        description="Individual policy validation results"
    )

    policy_failures: list[str] = Field(
        default_factory=list,
        description="Policy checks that failed"
    )

    manual_review_flags: list[str] = Field(
        default_factory=list,
        description="Conditions requiring manual review"
    )

    policy_version: str = Field(
        description="Policy version used for validation"
    )