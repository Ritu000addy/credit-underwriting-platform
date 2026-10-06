from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MandateCreate(BaseModel):
    application_id: str

    mandate_reference: str | None = None
    mandate_type: str | None = None
    provider: str | None = None


class MandateUpdate(BaseModel):
    status: str
    failure_reason: str | None = None
    completed_at: datetime | None = None


class MandateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    mandate_id: str
    application_id: str

    mandate_reference: str | None = None
    mandate_type: str | None = None
    provider: str | None = None

    status: str
    failure_reason: str | None = None

    initiated_at: datetime
    completed_at: datetime | None = None