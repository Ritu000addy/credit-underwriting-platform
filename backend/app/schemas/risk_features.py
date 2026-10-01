from pydantic import BaseModel

class CreditRiskFeatures(BaseModel):
    # Credit Bureau
    bureau_score: int | None = None
    dpd: int | None = None
    dpd_present: int | None = None
    credit_enquiries: int | None = None
    active_loans: int | None = None
    total_outstanding: float | None = None
    write_offs: float | None = None
    write_off_present: int | None = None
    outstanding_to_annual_income_ratio: float | None = None
    enquiries_to_active_loans_ratio: float | None = None

    # Internal History
    past_loan_count: int | None = None
    repayment_history_count: int | None = None
    repayment_history_coverage: float | None = None
    internal_dpd_count: int | None = None
    collection_count: int | None = None

    # Bank / Cash Flow
    monthly_credits: float | None = None
    monthly_debits: float | None = None
    net_monthly_cash_flow: float | None = None
    bank_balance: float | None = None
    existing_emi: float | None = None
    proposed_emi: float | None = None
    bounce_count: int | None = None
    transaction_count: int | None = None
    bounce_rate: float | None = None
    
    # Employment / Income
    monthly_salary: float | None = None
    employer: str | None = None
    emi_to_income_ratio: float | None = None
    cash_flow_to_income_ratio: float | None = None
    expense_to_income_ratio: float | None = None

    # Income Pattern
    income_trend: str | None = None    