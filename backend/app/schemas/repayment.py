from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class RepaymentScheduleGenerateRequest(BaseModel):
    application_id: str
    disbursement_id: str
    principal: Decimal
    annual_interest_rate: Decimal
    tenure_months: int
    first_due_date: datetime


class RepaymentScheduleResponse(BaseModel):
    repayment_schedule_id: str
    application_id: str
    disbursement_id: str
    installment_number: int
    due_date: datetime
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal
    outstanding_principal: Decimal
    status: str
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }

class RepaymentCreateRequest(BaseModel):
    application_id: str
    repayment_schedule_id: str
    repayment_amount: Decimal
    repayment_reference: str | None = None
    payment_mode: str | None = None
    payment_provider: str | None = None


class RepaymentResponse(BaseModel):
    repayment_id: str
    application_id: str
    repayment_schedule_id: str | None = None
    repayment_reference: str | None = None
    repayment_amount: Decimal
    payment_mode: str | None = None
    payment_provider: str | None = None
    principal_allocated: Decimal | None = None
    interest_allocated: Decimal | None = None
    status: str
    failure_reason: str | None = None
    paid_at: datetime | None = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }

class RepaymentSummaryResponse(BaseModel):
    application_id: str
    disbursement_id: str
    total_installments: int
    paid_installments: int
    pending_installments: int
    total_payable: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    next_pending_installment: int | None = None
    next_due_date: datetime | None = None
    next_due_amount: Decimal | None = None