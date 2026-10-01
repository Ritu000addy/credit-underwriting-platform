from pydantic.color import COLORS_BY_NAME
from decimal import Decimal

from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import (
    Borrower360,
    CreditBureauData,
    InternalHistoryData,
    BankCashFlowData,
    EmploymentBusinessData,
)

from backend.app.services.risk_assessment_service import risk_assessment_service

application = ApplicationCreate(
    application_id="LN102938",
    customer_id="CUST001",
    requested_amount=150000,
    loan_tenure_months=12,
)

borrower = Borrower360(
    customer_id="CUST001",

    credit_bureau=CreditBureauData(
        score=742,
        dpd=0,
        enquiries=2,
        active_loans=2,
        total_outstanding=250000,
        write_offs=0,        
    ),

    internal_history=InternalHistoryData(
        past_loans=[
            {"loan_id":"LOAN001"},
            {"loan_id":"LOAN002"},
        ],
        repayment=[
            {"loan_id":"LOAN001","status":"PAID"},
            {"loan_id":"LOAN002","status":"PAID"},
        ],
        dpd=[],
        collections=[],
    ),

    bank_cashflow=BankCashFlowData(
        credits=80000,
        debits=45000,
        balance=120000,
        emi=15000,
        bounce=0,
        transaction_count=120,
        income_pattern={
            "trend": "STABLE"
        },
    ),

    employment_business=EmploymentBusinessData(
        salary=80000,
        employer="Synthetic Employer",        
    ),
)

result = risk_assessment_service.assess(
    application,
    borrower,
)

print(result.model_dump())