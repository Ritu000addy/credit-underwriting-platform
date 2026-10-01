from pydantic import BaseModel, Field

class BankCashFlowCheck(BaseModel):
    check_id: str
    status: str
    reason: str

class EmploymentBusinessCheck(BaseModel):
    check_id: str
    status: str
    reason: str

class BankIncomeResult(BaseModel):
    status: str
    bank_cash_flow_checks: list[BankCashFlowCheck]
    employment_business_checks: list[EmploymentBusinessCheck]
    reason_codes: list[str] = Field(default_factory=list) 