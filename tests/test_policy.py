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
        "aadhaar":"123456789012",
        "ekyc_result": "VERIFIED",
        "dob": "1993-03-01",
        "address": "Pune",
    },
    credit_bureau={
        "score": 742,
        "dpd": 0,
        "enquiries": 2,
        "active_loans": 2,
        "write_offs": 0,
    },
    bank_cash_flow={
        "credits": 85000,
        "debits": 45000,
        "balance": 12000,
        "emi": 18000,
        "bounce": 0,
        "income_pattern": {
            "monthly_average": 85000,
            "trend": "STABLE",
        },
    },
    employment_business={
        "salary": 80000,
        "employer": "ABC Technologies",
        "gst": None,
        "udyam": None,
        "business_vintage": None,
    },
    internal_history={
        "past_loans": [
            {
                "load_id": "LOAN001",
                "status": "CLOSED",
            }
        ],
        "repayment": [
            {
                "loan_id": "LOAN001",
                "status": "ON_TIME",
            }
        ],
        "dpd": [],
        "collections": [],
    },

    device_behaviour={
        "device": "DEVICE_001",
        "ip" : "192.0.2.10",
        "velocity": {
            "applications_last_24h": 2,
        },
        "session_patterns": {
            "multiple_devices": False
        },
    },

    documents={
        "payslips": [
            {
                "document_id": "DOC001",
                "type": "PAYSLIP",
            }
        ],
        "bank_statements": [
            {
                "document_id": "DOC002",
                "type": "BANK_STATEMENT",
            }
        ],
        "invoices": [],
        "business_proofs": [],
    },
)

result = policy_engine.evaluate(
    application=application,
    borrower=borrower,
)

print(result.model_dump())