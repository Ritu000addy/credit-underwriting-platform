from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.completeness_checker import completeness_checker

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
        "address": "Pune",
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
    internal_history={
        "past_loans": [],
        "repayment": [],
        "dpd": [],
        "collections": [],
    },
    device_behaviour={
        "device": "DEVICE001",
        "ip": "192.168.1.10",
        "velocity": {},
        "session_patterns": {},
    },
    documents={
        "payslips": [],
        "bank_statements": [],
        "invoices": [],
        "business_proofs": [],
    },
)

result = completeness_checker.check(
    application=application,
    borrower=borrower,
)

print(result.model_dump())