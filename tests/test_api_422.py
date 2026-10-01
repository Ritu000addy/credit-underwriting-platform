from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json


payload = {
    "application": {
        "application_id": "API-TEST-001",
        "customer_id": "API-CUST-001",
        "loan_amount": 150000,
        "loan_tenure_months": 12,
        "annual_interest_rate": 12,
    },
    "borrower": {
        "customer_id": "API-CUST-001",
        "kyc": {
            "pan": "ABCDE1234F",
            "aadhaar": "123456789012",
            "ekyc_result": "VERIFIED",
            "dob": "1990-01-15",
        },
        "credit_bureau": {
            "score": 742,
            "dpd": 0,
            "enquiries": 2,
            "active_loans": 2,
            "total_outstanding": 200000,
            "write_offs": 0,
        },
        "bank_cash_flow": {
            "credits": 80000,
            "debits": 45000,
            "balance": 120000,
            "emi": 15000,
            "bounce": 0,
            "transaction_count": 30,
            "income_pattern": {
                "trend": "STABLE"
            },
        },
        "employment_business": {
            "salary": 80000,
            "employer": "TEST EMPLOYER",
        },
        "internal_history": {
            "past_loans": [{"loan_id": "L1"}],
            "repayment": [{"status": "PAID"}],
            "dpd": [],
            "collections": [],
        },
        "device_behaviour": {
            "device": "TEST-DEVICE",
            "ip": "127.0.0.1",
            "velocity": {
                "applications_last_24h": 1
            },
            "session_patterns": {
                "multiple_devices": False
            },
        },
        "documents": {
            "payslips": [{"verified": True}],
            "bank_statements": [{"verified": True}],
        },
    },
}


request = Request(
    "http://127.0.0.1:8000/underwriting/evaluate",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)


try:
    response = urlopen(request)
    print("STATUS:", response.status)
    print(json.dumps(
        json.loads(response.read()),
        indent=2,
    ))

except HTTPError as error:
    print("STATUS:", error.code)
    print(error.read().decode())