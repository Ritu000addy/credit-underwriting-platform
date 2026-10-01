from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CollectionCreateRequest(BaseModel):
    application_id: str
    repayment_schedule_id: str | None = None

    collection_type: str

    due_amount: Decimal
    collected_amount: Decimal
    outstanding_amount: Decimal

    days_past_due: int
    status: str

    collection_reference: str | None = None
    collection_channel: str | None = None
    remarks: str | None = None
    collected_at: datetime | None = None


class CollectionResponse(BaseModel):
    collection_id: str
    application_id: str
    repayment_schedule_id: str | None = None

    collection_type: str

    due_amount: Decimal
    collected_amount: Decimal
    outstanding_amount: Decimal

    days_past_due: int
    status: str

    collection_reference: str | None = None
    collection_channel: str | None = None
    remarks: str | None = None
    collected_at: datetime | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

class CollectionSummaryResponse(BaseModel):
    application_id: str
    repayment_schedule_id: str

    total_due: Decimal
    total_collected: Decimal
    total_outstanding: Decimal

    days_past_due: int
    status: str | None = None

class ApplicationOverdueSummaryResponse(BaseModel):
    application_id: str
    total_overdue_installments: int
    total_overdue_amount: Decimal
    maximum_days_past_due: int
    current_dpd_bucket: str
    collection_stage: str
    oldest_overdue_due_date: datetime | None = None

class CollectionRecordRequest(BaseModel):
    application_id: str
    repayment_schedule_id: str

    repayment_amount: Decimal

    collection_reference: str | None = None
    collection_channel: str | None = None

    payment_mode: str | None = None
    payment_provider: str | None = None

    remarks: str | None = None


class CollectionRecordResponse(CollectionResponse):
    pass