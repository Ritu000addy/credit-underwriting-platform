from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.policy_engine import policy_engine


def test_policy_engine_governed_refer_path():
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
            "score": 742,
            "dpd": 0,
            "enquiries": 2,
            "active_loans": 2,
            "write_offs": 0,
            "total_outstanding": 100000,
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
            "ip": "192.0.2.10",
            "velocity": {
                "applications_last_24h": 2,
            },
            "session_patterns": {
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

    policy_config = {
        "age": {
            "min_age": 21,
            "max_age": 60,
        },
        "income": {
            "minimum_income": 25000,
        },
        "geography": {
            "serviceable_states": [],
            "serviceable_cities": [],
            "serviceable_pincodes": [],
        },
        "bureau": {
            "minimum_score": 650,
        },
        "exposure": {
            "maximum_exposure": 500000,
        },
        "foir": {
            "maximum_foir": 50,
        },
        "vintage": {
            "minimum_vintage": None,
        },
        "kyc_bank_validation": {
            "pan_required": True,
            "ekyc_required": True,
            "required_ekyc_result": "VERIFIED",
            "aadhaar_kyc_required": False,
        },
        "loan": {
            "minimum_amount": 50000,
            "maximum_amount": 500000,
            "minimum_tenure_months": 6,
            "maximum_tenure_months": 60,
        },
        "exceptions": {
            "enabled": False,
            "rules": [],
        },
    }

    policy_metadata = {
        "policy_version": "POL-2026.09",
        "effective_from": "2026-09-01T00:00:00",
        "effective_to": None,
    }

    result = policy_engine.evaluate(
        application=application,
        borrower=borrower,
        policy_config=policy_config,
        policy_metadata=policy_metadata,
    )

    assert result.policy_status == "REFER"
    assert result.policy_version == "POL-2026.09"
    assert result.effective_from == "2026-09-01T00:00:00"
    assert result.effective_to is None

    rules = {rule.rule_id: rule for rule in result.rules}

    assert rules["AGE"].status == "PASS"
    assert rules["INCOME_ELIGIBILITY"].status == "PASS"
    assert rules["BUREAU"].status == "PASS"
    assert rules["EXPOSURE"].status == "PASS"
    assert rules["LOAN_AMOUNT_TENURE"].status == "PASS"
    assert rules["KYC_BANK_VALIDATION"].status == "PASS"

    assert rules["GEOGRAPHY"].status == "NOT_EVALUATED"
    assert rules["FOIR_DTI"].status == "NOT_EVALUATED"
    assert rules["VINTAGE_REPAYMENT"].status == "NOT_EVALUATED"
    assert rules["POLICY_EXCEPTION"].status == "NOT_EVALUATED"