from datetime import datetime

from pydantic import BaseModel


class ManualReviewCreate(BaseModel):
    application_id: str
    review_reason: str | None = None


class ManualReviewResponse(BaseModel):
    review_id: str
    application_id: str
    review_status: str
    review_reason: str | None = None
    reviewer_id: str | None = None
    reviewer_decision: str | None = None
    reviewer_remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class ManualReviewDecision(BaseModel):
    reviewer_id: str
    reviewer_decision: str
    reviewer_remarks: str | None = None