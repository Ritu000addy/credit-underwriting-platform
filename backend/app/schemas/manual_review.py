from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ManualReviewCreate(BaseModel):
    application_id: str
    review_reason: str | None = None

    @field_validator("application_id")
    @classmethod
    def validate_application_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("APPLICATION_ID_REQUIRED")

        return value

    @field_validator("review_reason")
    @classmethod
    def validate_review_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("MANUAL_REVIEW_REASON_REQUIRED")

        if len(value) > 1000:
            raise ValueError("MANUAL_REVIEW_REASON_TOO_LONG")

        return value


class ManualReviewStart(BaseModel):
    reviewer_id: str

    @field_validator("reviewer_id")
    @classmethod
    def validate_reviewer_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("REVIEWER_ID_REQUIRED")

        if len(value) > 100:
            raise ValueError("REVIEWER_ID_TOO_LONG")

        return value


class ManualReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: str
    application_id: str
    review_status: str
    review_reason: str | None = None

    reviewer_id: str | None = None
    reviewer_decision: str | None = None
    reviewer_remarks: str | None = None

    maker_checker_required: bool

    checker_id: str | None = None
    checker_decision: str | None = None
    checker_remarks: str | None = None
    checker_completed_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class ManualReviewRecommendation(BaseModel):
    reviewer_id: str
    reviewer_decision: str
    reviewer_remarks: str | None = None

    @field_validator("reviewer_id")
    @classmethod
    def validate_reviewer_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("REVIEWER_ID_REQUIRED")

        if len(value) > 100:
            raise ValueError("REVIEWER_ID_TOO_LONG")

        return value

    @field_validator("reviewer_decision")
    @classmethod
    def validate_reviewer_decision(cls, value: str) -> str:
        value = value.strip().upper()

        if value not in {"APPROVE", "REJECT"}:
            raise ValueError("REVIEWER_DECISION_INVALID")

        return value

    @field_validator("reviewer_remarks")
    @classmethod
    def validate_reviewer_remarks(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if len(value) > 2000:
            raise ValueError("REVIEWER_REMARKS_TOO_LONG")

        return value


class ManualReviewCheckerDecision(BaseModel):
    checker_id: str
    checker_decision: str
    checker_remarks: str | None = None

    @field_validator("checker_id")
    @classmethod
    def validate_checker_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("CHECKER_ID_REQUIRED")

        if len(value) > 100:
            raise ValueError("CHECKER_ID_TOO_LONG")

        return value

    @field_validator("checker_decision")
    @classmethod
    def validate_checker_decision(cls, value: str) -> str:
        value = value.strip().upper()

        if value not in {"APPROVE", "REJECT"}:
            raise ValueError("CHECKER_DECISION_INVALID")

        return value

    @field_validator("checker_remarks")
    @classmethod
    def validate_checker_remarks(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if len(value) > 2000:
            raise ValueError("CHECKER_REMARKS_TOO_LONG")

        return value