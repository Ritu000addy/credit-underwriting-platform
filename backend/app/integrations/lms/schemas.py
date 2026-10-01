from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class LMSSanctionRequest(BaseModel):
    sanction_id: str
    application_id: str
    sanctioned_amount: Decimal
    sanctioned_tenure: int
    sanctioned_emi: Decimal | None = None
    interest_rate: Decimal | None = None
    sanction_status: str
    approval_authority: str | None = None
    sanctioned_at: datetime
    expires_at: datetime | None = None


class LMSSanctionResponse(BaseModel):
    loan_account_id: str
    application_id: str
    sanction_id: str
    loan_status: str
    created_at: datetime

class LMSRepaymentScheduleRequest(BaseModel):
    loan_account_id: str
    application_id: str
    sanction_id: str


class LMSRepaymentScheduleResponse(BaseModel):
    repayment_schedule_id: str
    loan_account_id: str
    application_id: str
    schedule_status: str
    created_at: datetime

class LMSServicingInstallmentRequest(BaseModel):
    loan_account_id: str
    application_id: str
    repayment_schedule_id: str
    installment_number: int
    due_date: datetime
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal


class LMSServicingInstallmentResponse(BaseModel):
    repayment_schedule_id: str
    loan_account_id: str
    installment_number: int
    schedule_status: str

class LMSLoanStatusRequest(BaseModel):
    loan_account_id: str
    application_id: str
    loan_status: str


class LMSLoanStatusResponse(BaseModel):
    loan_account_id: str
    application_id: str
    loan_status: str
    updated_at: datetime