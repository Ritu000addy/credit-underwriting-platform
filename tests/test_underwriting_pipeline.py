from decimal import Decimal

from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360

from backend.app.services.underwriting_pipeline import underwriting_pipeline

application = ApplicationCreate(
    application_id="APP001",
    customer_id="CUS001",
    requested_amount=500000,
    loan_tenure_months=36,
    annual_interest_rate=Decimal("12"),
)

borrower = Borrower360(
    customer_id="CUS001",

    kyc = {
        "pan": "ABCDE1234F",
        "aadhaar": "123456789012",
        "ekyc_result": "VERIFIED",
        "dob": "1993-03-01",
        "address": "Pune",
    },
    credit_bureau={
        "score": 742,
        "dpd": 0,
        "enquiries": 2,
        "active_loans": 2,
        "total_outstanding": 250000,
        "write_offs": 0,
    },
    bank_cash_flow={
        "credits": 85000,
        "debits": 45000,
        "balance": 120000,
        "emi": 18000,
        "bounce": 0,
        "transaction_count": 120,
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
                "loan_id": "LOAN001",
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
            "applications_last_7d": 3,
        },
        "session_patterns": {
            "session_duration_seconds": 420,
            "multiple_devices": False,
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

result = underwriting_pipeline.process(
    application=application,
    borrower=borrower,
)

print(result.model_dump())