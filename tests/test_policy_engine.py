from datetime import datetime

from backend.app.database import SessionLocal

from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.policy_engine import policy_engine

from backend.app.services.policy_version_service import (
    policy_version_service,
)

def test_policy_engine_uses_governed_policy():
    db = SessionLocal()

    try:
        policy_context = policy_version_service.get_policy_context(
            db=db,
            as_of=datetime.utcnow(),
        )

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
                "aadhaar_kyc_status": "VERIFIED",
                "ekyc_result": "VERIFIED",
                "dob": "1993-03-01",
                "address": "Pune, Maharashtra",
            },
            credit_bureau={
                "score": 750,
                "dpd": 0,
                "enquiries": 2,
                "active_loans": 1,
                "total_outstanding": 100000,
                "write_offs": 0,
            },
            bank_cash_flow={
                "credits": 100000,
                "debits": 40000,
                "balance": 60000,
                "emi": 15000,
                "bounce": 0,
                "transaction_count": 30,
            },
            employment_business={
                "salary": 75000,
                "employer": "ABC Company",
                "business_vintage": 24,
            },
            internal_history={
                "past_loans": [{"loan_id": "L1"}],
                "repayment": [{"status": "PAID"}],
                "dpd": [],
                "collections": [],
            },
            device_behaviour={
                "device": "TEST-DEVICE",
                "ip": "127.0.0.1",
                "velocity": {
                    "applications_last_24h": 1
                },
                "session_patterns": {
                    "multiple_devices": False
                },
            },
            documents={
                "payslips": [{"verified": True}],
                "bank_statements": [{"verified": True}],
            },
        )

        result = policy_engine.evaluate(
            application=application,
            borrower=borrower,
            foir=30,
            policy_config=policy_context["policy_config"],
            policy_metadata=policy_context["policy_metadata"],
        )

        rule_map = {
            rule.rule_id: rule
            for rule in result.rules
        }

        assert result.policy_version == "POL-2026.09"

        assert rule_map["AGE"].status == "PASS"
        assert rule_map["INCOME_ELIGIBILITY"].status == "PASS"
        assert rule_map["BUREAU"].status == "PASS"
        assert rule_map["EXPOSURE"].status == "PASS"
        assert rule_map["FOIR_DTI"].status == "PASS"
        assert rule_map["KYC_BANK_VALIDATION"].status == "PASS"
        assert rule_map["LOAN_AMOUNT_TENURE"].status == "PASS"

    finally:
        db.close()