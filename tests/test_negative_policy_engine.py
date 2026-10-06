import pytest
from datetime import datetime

from backend.app.database import SessionLocal
from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.services.policy_engine import policy_engine
from backend.app.services.policy_version_service import (
    policy_version_service,
)

def get_policy_context():
    db = SessionLocal()

    try:
        return policy_version_service.get_policy_context(
            db=db,
            as_of=datetime.utcnow(),
        )
    finally:
        db.close()


def build_application(
    requested_amount=150000,
    loan_tenure_months=12,
):
    return ApplicationCreate(
        application_id="NEG-APP-001",
        customer_id="NEG-CUST-001",
        requested_amount=requested_amount,
        loan_tenure_months=loan_tenure_months,
    )


def build_borrower(
    dob="1993-03-01",
    pan="ABCDE1234F",
    ekyc_result="VERIFIED",
    bureau_score=750,
    total_outstanding=100000,
    salary=75000,
):
    return Borrower360(
        customer_id="NEG-CUST-001",
        kyc={
            "pan": pan,
            "aadhaar": "123456789012",
            "aadhaar_kyc_status": "VERIFIED",
            "ekyc_result": ekyc_result,
            "dob": dob,
            "address": "Pune, Maharashtra",
        },
        credit_bureau={
            "score": bureau_score,
            "dpd": 0,
            "enquiries": 2,
            "active_loans": 1,
            "total_outstanding": total_outstanding,
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
            "salary": salary,
            "employer": "TEST EMPLOYER",
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
                "applications_last_24h": 1,
            },
            "session_patterns": {
                "multiple_devices": False,
            },
        },
        documents={
            "payslips": [{"verified": True}],
            "bank_statements": [{"verified": True}],
        },
    )


def evaluate(
    application=None,
    borrower=None,
    foir=30,
    policy_config=None,
    policy_metadata=None,
):
    context = get_policy_context()

    return policy_engine.evaluate(
        application=application or build_application(),
        borrower=borrower or build_borrower(),
        foir=foir,
        policy_config=(
            policy_config
            if policy_config is not None
            else context["policy_config"]
        ),
        policy_metadata=(
            policy_metadata
            if policy_metadata is not None
            else context["policy_metadata"]
        ),
    )


def get_rule(result, rule_id):
    return next(
        rule
        for rule in result.rules
        if rule.rule_id == rule_id
    )


def test_missing_policy_config_is_rejected():
    with pytest.raises(
        ValueError,
        match="GOVERNED_POLICY_CONFIG_REQUIRED",
    ):
        policy_engine.evaluate(
            application=build_application(),
            borrower=build_borrower(),
            foir=30,
            policy_metadata={
                "policy_version": "POL-2026.09"
            },
        )

def test_missing_policy_metadata_is_rejected():
    context = get_policy_context()

    with pytest.raises(
        ValueError,
        match="GOVERNED_POLICY_METADATA_REQUIRED",
    ):
        policy_engine.evaluate(
            application=build_application(),
            borrower=build_borrower(),
            foir=30,
            policy_config=context["policy_config"],
        )


def test_age_below_minimum_fails():
    result = evaluate(
        borrower=build_borrower(
            dob="2007-01-01"
        )
    )

    assert get_rule(result, "AGE").status == "FAIL"


def test_bureau_below_minimum_fails():
    context = get_policy_context()

    minimum_score = context["policy_config"]["bureau"][
        "minimum_score"
    ]

    result = evaluate(
        borrower=build_borrower(
            bureau_score=minimum_score - 1
        )
    )

    assert get_rule(result, "BUREAU").status == "FAIL"


def test_exposure_above_maximum_fails():
    context = get_policy_context()

    maximum_exposure = context["policy_config"]["exposure"][
        "maximum_exposure"
    ]

    result = evaluate(
        borrower=build_borrower(
            total_outstanding=maximum_exposure + 1
        )
    )

    assert get_rule(result, "EXPOSURE").status == "FAIL"


def test_foir_above_maximum_fails():
    context = get_policy_context()

    maximum_foir = context["policy_config"]["foir"][
        "maximum_foir"
    ]
    result = evaluate(
        foir=maximum_foir + 0.01
    )

    assert get_rule(result, "FOIR_DTI").status == "FAIL"


def test_missing_pan_fails_kyc():
    result = evaluate(
        borrower=build_borrower(pan=None)
    )

    assert (
        get_rule(
            result,
            "KYC_BANK_VALIDATION",
        ).status
        == "FAIL"
    )


def test_loan_amount_above_maximum_fails():
    context = get_policy_context()

    maximum_amount = context["policy_config"]["loan"][
        "maximum_amount"
    ]

    result = evaluate(
        application=build_application(
            requested_amount=maximum_amount + 1
        )
    )

    assert (
        get_rule(
            result,
            "LOAN_AMOUNT_TENURE",
        ).status
        == "FAIL"
    )


def test_loan_tenure_above_maximum_fails():
    context = get_policy_context()

    maximum_tenure = context["policy_config"]["loan"][
        "maximum_tenure_months"
    ]

    result = evaluate(
        application=build_application(
            loan_tenure_months=maximum_tenure + 1
        )
    )

    assert (
        get_rule(
            result,
            "LOAN_AMOUNT_TENURE",
        ).status
        == "FAIL"
    )


def test_unconfigured_geography_is_not_evaluated():
    result = evaluate()

    assert (
        get_rule(
            result,
            "GEOGRAPHY",
        ).status
        == "NOT_EVALUATED"
    )


def test_unconfigured_vintage_is_not_evaluated():
    result = evaluate()

    assert (
        get_rule(
            result,
            "VINTAGE_REPAYMENT",
        ).status
        == "NOT_EVALUATED"
    )


def test_policy_rejects_when_rule_fails():
    context = get_policy_context()

    minimum_score = context["policy_config"]["bureau"][
        "minimum_score"
    ]

    result = evaluate(
        borrower=build_borrower(
            bureau_score=minimum_score - 1
        )
    )

    assert result.policy_status == "REJECT"


def test_policy_refers_when_required_rule_not_evaluated():
    result = evaluate()

    assert result.policy_status == "REFER"