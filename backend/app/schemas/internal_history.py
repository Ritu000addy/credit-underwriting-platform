from pydantic import BaseModel
from typing import Optional


class InternalHistoryCreate(BaseModel):
    application_id: str

    previous_loans_count: Optional[int] = None
    active_loans_count: Optional[int] = None
    closed_loans_count: Optional[int] = None

    total_previous_exposure: Optional[float] = None
    total_outstanding_amount: Optional[float] = None

    repayment_history: Optional[str] = None
    dpd_count: Optional[int] = None
    max_dpd: Optional[int] = None
    overdue_amount: Optional[float] = None

    write_off_count: Optional[int] = None
    settlement_count: Optional[int] = None

    last_loan_date: Optional[str] = None
    analysis_reference: Optional[str] = None