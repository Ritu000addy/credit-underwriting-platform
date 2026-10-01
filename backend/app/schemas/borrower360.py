from typing import Any
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

class KYCData(BaseModel):
    pan: str | None = None
    aadhaar: str | None = None
    aadhaar_kyc_status: str | None = None
    ekyc_result: str | None = None
    address: str | None = None
    dob: date | None = None
    customer_identifiers: dict[str, str] = Field(default_factory=dict)

class CreditBureauData(BaseModel):
    score: int | None = None
    dpd: int | None = None
    enquiries: int | None = None
    active_loans: int | None = None
    total_outstanding: Decimal | None = None
    write_offs: Decimal | None = None

class BankCashFlowData(BaseModel):
    credits: Decimal | None = None
    debits: Decimal | None = None
    balance: Decimal | None = None
    emi: Decimal | None = None
    bounce: int | None = None
    transaction_count: int | None = None
    income_pattern: dict[str, Any] | None = None

class EmploymentBusinessData(BaseModel):
    salary: Decimal | None = None
    employer: str | None = None
    gst: str | None = None
    udyam: str | None = None
    business_vintage: int | None = None

class InternalHistoryData(BaseModel):
    past_loans: list[dict[str, Any]] = Field(default_factory=list)
    repayment: list[dict[str, Any]] = Field(default_factory=list)
    dpd: list[dict[str, Any]] = Field(default_factory=list)
    collections: list[dict[str, Any]] = Field(default_factory=list)

class DeviceBehaviourData(BaseModel):
    device: str | None = None
    ip: str | None = None
    velocity: Any = None
    session_patterns: dict[str, Any] | None = None

class DocumentData(BaseModel):
    payslips: list[dict[str, Any]] = Field(default_factory=list)
    bank_statements: list[dict[str, Any]] = Field(default_factory=list)
    invoices: list[dict[str, Any]] = Field(default_factory=list)
    business_proofs: list[dict[str, Any]] = Field(default_factory=list)

class Borrower360(BaseModel):
    customer_id: str

    kyc: KYCData | None = None
    credit_bureau: CreditBureauData | None = None
    bank_cash_flow: BankCashFlowData | None = None
    employment_business: EmploymentBusinessData | None = None
    internal_history: InternalHistoryData | None = None
    device_behaviour: DeviceBehaviourData | None = None
    documents: DocumentData | None = None