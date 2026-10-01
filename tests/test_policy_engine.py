from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.policy_engine import policy_engine

application = ApplicationCreate(
    application_id="APP001",
    customer_id="CUS001",
    requested_amount=500000,
    loan_tenure_months=36,
)

borrower = Borrower360(
    customer_id="CUS001",
    kyc={
        "pan": "ABCDE1234F",
        "aadhaar": "123456789012",
        "ekyc_result": "VERIFIED",
        "dob": "1993-03-01",
    },
    credit_bureau={
        "score": 750,
        "dpd": 0,
        "enquiries": 2,
        "active_loans": 1,
    },
    bank_cash_flow={
        "credits": 100000,
        "debits": 40000,
        "balance": 60000,
        "emi": 15000,
        "bounce": 0,
    },
    employment_business={
        "salary": 75000,
        "employer": "ABC Company",
    },
)

result = policy_engine.evaluate(
    application=application,
    borrower=borrower,
    )

print(result.model_dump())