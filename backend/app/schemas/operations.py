from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class StatusCounts(BaseModel):
    total: int
    by_status: dict[str, int]


class CollectionOperationsSummary(BaseModel):
    overdue_schedule_count: int
    overdue_application_count: int
    overdue_outstanding_amount: Decimal


class OperationsDashboardResponse(BaseModel):
    generated_at: datetime
    applications: StatusCounts
    underwriting: StatusCounts
    manual_review: StatusCounts
    exceptions: StatusCounts
    disbursements: StatusCounts
    collections: CollectionOperationsSummary
    reconciliation: StatusCounts
    operations_queue: StatusCounts


class OperationsApplicationResponse(BaseModel):
    application_id: str
    customer_id: str
    product: str | None = None
    requested_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    decision: str | None = None
    risk_grade: str | None = None
    policy_version: str | None = None

    manual_review_status: str | None = None
    exception_status: str | None = None

    sanction_status: str | None = None

    agreement_status: str | None = None
    esign_status: str | None = None

    mandate_status: str | None = None

    disbursement_status: str | None = None
    disbursement_amount: Decimal | None = None

    repayment_status: str | None = None
    collection_status: str | None = None
    overdue_amount: Decimal | None = None
    days_past_due: int | None = None

    reconciliation_status: str | None = None


class OperationsApplicationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[OperationsApplicationResponse]


class OperationsManualReviewResponse(BaseModel):
    review_id: str
    application_id: str
    review_status: str
    review_reason: str | None = None
    reviewer_id: str | None = None
    reviewer_decision: str | None = None
    reviewer_remarks: str | None = None
    checker_id: str | None = None
    checker_decision: str | None = None
    checker_remarks: str | None = None
    maker_checker_required: bool
    created_at: datetime
    updated_at: datetime


class OperationsExceptionResponse(BaseModel):
    exception_id: str
    review_id: str
    application_id: str
    exception_type: str
    description: str
    status: str
    assigned_to: str | None = None
    created_by: str
    requested_information: str | None = None
    resolution_action: str | None = None
    resolution_remarks: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OperationsDisbursementResponse(BaseModel):
    disbursement_id: str
    application_id: str
    sanction_id: str | None = None
    disbursement_amount: Decimal
    beneficiary_reference: str | None = None
    bank_reference: str | None = None
    payment_provider: str | None = None
    status: str
    failure_reason: str | None = None
    retry_attempts: int
    initiated_at: datetime | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OperationsReconciliationResponse(BaseModel):
    reconciliation_id: str
    application_id: str | None = None
    disbursement_id: str | None = None
    transaction_type: str
    internal_reference: str | None = None
    external_reference: str | None = None
    transaction_amount: Decimal
    transaction_date: datetime | None = None
    reconciliation_status: str
    mismatch_reason: str | None = None
    reconciled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OperationsOverdueCollectionResponse(BaseModel):
    collection_id: str
    application_id: str
    repayment_schedule_id: str | None = None
    collection_type: str | None = None
    due_amount: Decimal
    collected_amount: Decimal
    outstanding_amount: Decimal
    days_past_due: int
    status: str
    collection_reference: str | None = None
    collection_channel: str | None = None
    created_at: datetime
    updated_at: datetime