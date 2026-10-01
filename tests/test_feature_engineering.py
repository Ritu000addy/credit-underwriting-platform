from backend.app.schemas.borrower360 import (
    Borrower360,
    CreditBureauData,
    InternalHistoryData,
    BankCashFlowData,
    EmploymentBusinessData,
)

from backend.app.services.feature_engineering import (
    feature_engineering_service,
)

borrower = Borrower360(
    customer_id="CUS001",

    credit_bureau=CreditBureauData(
        score=742,
        dpd=0,
        enquiries=2,
        active_loans=2,
        total_outstanding=250000,
        write_offs=0.0,
    ),

    internal_history=InternalHistoryData(
        past_loans=[
            {"loan_id":"LOAN001"},
            {"loan_id": "LOAN002"},
        ],
        repayment=[
            {"load_id": "LOAN001", "status":"PAID"},
            {"load_id": "LOAN002", "status":"PAID"},
        ],
        dpd= [],
        collections= [],
    ),

    bank_cash_flow = BankCashFlowData(
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

    employment_business = EmploymentBusinessData(
        salary=80000,
        employer="Synthetic Employer",
    ),

)

features = feature_engineering_service.build_credit_features(
    borrower
)

print(features.model_dump())