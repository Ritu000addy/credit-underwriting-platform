from decimal import Decimal

from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.completeness import CompletenessResult
from backend.app.schemas.kyc import KYCCheckResult
from backend.app.schemas.bureau_history import BureauHistoryResult
from backend.app.schemas.bank_income import BankIncomeResult
from backend.app.schemas.fraud import FraudScreeningResult

from backend.app.services.completeness_checker import completeness_checker
from backend.app.services.kyc_validator import kyc_validator
from backend.app.services.bureau_history_validator import (
    bureau_history_validator,
)
from backend.app.services.bank_income_validator import bank_income_validator
from backend.app.services.fraud_validator import fraud_validator
from backend.app.services.underwriting_pipeline import UnderwritingPipeline


POLICY_METADATA = {
    "policy_version": "POLICY-TEST-01",
    "effective_from": "2026-10-01T00:00:00",
    "effective_to": None,
}


def make_application():
    return ApplicationCreate(
        application_id="APP-EARLY-REFERRAL-TEST",
        customer_id="CUST-EARLY-REFERRAL-TEST",
        requested_amount=Decimal("150000"),
        loan_tenure_months=12,
        annual_interest_rate=Decimal("12.00"),
    )


def make_borrower():
    return Borrower360(
        customer_id="CUST-EARLY-REFERRAL-TEST",
    )


def run_pipeline():
    return UnderwritingPipeline().process(
        application=make_application(),
        borrower=make_borrower(),
        policy_config={},
        policy_metadata=POLICY_METADATA,
    )


def assert_review_decision(result, expected_reason_code):
    assert result.decision is not None
    assert result.decision.decision == "REFER"
    assert expected_reason_code in result.decision.reason_codes

    # No risk or policy assessment should be fabricated after an early exit.
    assert result.risk_assessment is None
    assert result.policy is None
    assert result.decision.credit_score is None
    assert result.decision.probability_of_default is None
    assert result.decision.recommended_amount is None


def test_incomplete_application_generates_refer(monkeypatch):
    monkeypatch.setattr(
        completeness_checker,
        "check",
        lambda *_: CompletenessResult(
            status="INCOMPLETE",
            missing_fields=["documents"],
        ),
    )

    result = run_pipeline()

    assert_review_decision(result, "APPLICATION_DATA_INCOMPLETE")
    assert "REQUIRED_DATA_MISSING_DOCUMENTS" in result.decision.reason_codes


def test_failed_kyc_generates_refer(monkeypatch):
    monkeypatch.setattr(
        completeness_checker,
        "check",
        lambda *_: CompletenessResult(status="COMPLETE", missing_fields=[]),
    )
    monkeypatch.setattr(
        kyc_validator,
        "validate",
        lambda *_args, **_kwargs: KYCCheckResult(
            status="FAIL",
            checks=[],
            reason_codes=["KYC_EKYC_NOT_VERIFIED"],
        ),
    )

    result = run_pipeline()

    assert_review_decision(result, "KYC_REVIEW_REQUIRED")
    assert "KYC_EKYC_NOT_VERIFIED" in result.decision.reason_codes


def test_unverified_bureau_generates_refer(monkeypatch):
    monkeypatch.setattr(
        completeness_checker,
        "check",
        lambda *_: CompletenessResult(status="COMPLETE", missing_fields=[]),
    )
    monkeypatch.setattr(
        kyc_validator,
        "validate",
        lambda *_args, **_kwargs: KYCCheckResult(
            status="PASS",
            checks=[],
            reason_codes=[],
        ),
    )
    monkeypatch.setattr(
        bureau_history_validator,
        "validate",
        lambda *_: BureauHistoryResult(
            status="FAIL",
            bureau_checks=[],
            internal_history_checks=[],
            reason_codes=["BUREAU_DATA_NOT_VERIFIED"],
        ),
    )

    result = run_pipeline()

    assert_review_decision(result, "BUREAU_HISTORY_REVIEW_REQUIRED")
    assert "BUREAU_DATA_NOT_VERIFIED" in result.decision.reason_codes


def test_unverified_bank_data_generates_refer(monkeypatch):
    monkeypatch.setattr(
        completeness_checker,
        "check",
        lambda *_: CompletenessResult(status="COMPLETE", missing_fields=[]),
    )
    monkeypatch.setattr(
        kyc_validator,
        "validate",
        lambda *_args, **_kwargs: KYCCheckResult(
            status="PASS",
            checks=[],
            reason_codes=[],
        ),
    )
    monkeypatch.setattr(
        bureau_history_validator,
        "validate",
        lambda *_: BureauHistoryResult(
            status="PASS",
            bureau_checks=[],
            internal_history_checks=[],
            reason_codes=[],
        ),
    )
    monkeypatch.setattr(
        bank_income_validator,
        "validate",
        lambda *_: BankIncomeResult(
            status="FAIL",
            bank_cash_flow_checks=[],
            employment_business_checks=[],
            reason_codes=["BANK_DATA_NOT_VERIFIED"],
        ),
    )

    result = run_pipeline()

    assert_review_decision(result, "BANK_INCOME_REVIEW_REQUIRED")
    assert "BANK_DATA_NOT_VERIFIED" in result.decision.reason_codes


def test_failed_fraud_screening_generates_refer(monkeypatch):
    monkeypatch.setattr(
        completeness_checker,
        "check",
        lambda *_: CompletenessResult(status="COMPLETE", missing_fields=[]),
    )
    monkeypatch.setattr(
        kyc_validator,
        "validate",
        lambda *_args, **_kwargs: KYCCheckResult(
            status="PASS",
            checks=[],
            reason_codes=[],
        ),
    )
    monkeypatch.setattr(
        bureau_history_validator,
        "validate",
        lambda *_: BureauHistoryResult(
            status="PASS",
            bureau_checks=[],
            internal_history_checks=[],
            reason_codes=[],
        ),
    )
    monkeypatch.setattr(
        bank_income_validator,
        "validate",
        lambda *_: BankIncomeResult(
            status="PASS",
            bank_cash_flow_checks=[],
            employment_business_checks=[],
            reason_codes=[],
        ),
    )
    monkeypatch.setattr(
        fraud_validator,
        "validate",
        lambda *_: FraudScreeningResult(
            status="FAIL",
            checks=[],
            reason_codes=["FRAUD_SCREENING_INCOMPLETE"],
        ),
    )

    result = run_pipeline()

    assert_review_decision(result, "FRAUD_SCREENING_REVIEW_REQUIRED")
    assert "FRAUD_SCREENING_INCOMPLETE" in result.decision.reason_codes