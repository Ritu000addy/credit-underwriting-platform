from decimal import Decimal

from backend.app.schemas.borrower360 import (
    Borrower360,
    KYCData,
    BankCashFlowData,
    DeviceBehaviourData,
    DocumentData,
)

from backend.app.schemas.policy import PolicyEvaluationResult
from backend.app.schemas.risk_assessment import RiskAssessmentResult

from backend.app.services.fraud_feature_engineering import (
    fraud_feature_engineering_service,
)
from backend.app.services.fraud_rules_engine import FraudRulesEngine
from backend.app.services.fraud_scoring_service import FraudScoringService
from backend.app.services.fraud_validator import FraudValidator
from backend.app.services.decision_orchestrator import DecisionOrchestrator


def make_borrower():
    return Borrower360(
        customer_id="FRAUD-CONTROL-TEST",
        kyc=KYCData(
            pan="ABCDE1234F",
            ekyc_result="VERIFIED",
            dob="1993-03-01",
        ),
        bank_cash_flow=BankCashFlowData(
            transaction_count=120,
        ),
        device_behaviour=DeviceBehaviourData(
            device="SYNTHETIC-DEVICE",
            ip="192.0.2.10",
            velocity={"applications_last_24h": 2},
            session_patterns={
                "multiple_devices": False,
                "login_count": 2,
            },
        ),
        documents=DocumentData(
            bank_statements=[{"document_id": "SYNTHETIC-DOC-1"}],
        ),
    )


def make_policy(status):
    return PolicyEvaluationResult(
        policy_status=status,
        policy_version="TEST-POLICY-01",
        effective_from="2026-10-01T00:00:00",
        effective_to=None,
        rules=[],
    )


def make_risk_result(
    *,
    fraud_score,
    fraud_risk_level,
    fraud_confidence,
    fraud_reason_codes=None,
):
    return RiskAssessmentResult(
        status="COMPLETE",
        credit_score=742,
        probability_of_default=Decimal("0.02"),
        fraud_score=fraud_score,
        fraud_risk_level=fraud_risk_level,
        fraud_confidence=fraud_confidence,
        fraud_reason_codes=fraud_reason_codes or [],
    )


def test_unimplemented_detectors_are_not_marked_clean():
    borrower = make_borrower()
    features = fraud_feature_engineering_service.build_features(
        borrower
    )

    assert features.identity_mismatch_flag is None
    assert features.transaction_anomaly_flag is None
    assert features.document_anomaly_flag is None
    assert features.session_anomaly_flag is None

    rules = FraudRulesEngine().evaluate(features)
    rule_statuses = {rule.rule_id: rule.status for rule in rules}

    assert rule_statuses["IDENTITY_MISMATCH"] == "NOT_EVALUATED"
    assert rule_statuses["DEVICE_VELOCITY"] == "PASS"
    assert rule_statuses["MULTIPLE_DEVICE"] == "PASS"
    assert rule_statuses["TRANSACTION_ANOMALY"] == "NOT_EVALUATED"
    assert rule_statuses["DOCUMENT_ANOMALY"] == "NOT_EVALUATED"
    assert rule_statuses["SESSION_BEHAVIOUR"] == "NOT_EVALUATED"


def test_incomplete_fraud_evidence_has_no_false_low_risk_score():
    borrower = make_borrower()
    features = fraud_feature_engineering_service.build_features(
        borrower
    )
    rules = FraudRulesEngine().evaluate(features)

    result = FraudScoringService().calculate(
        features=features,
        rule_results=rules,
    )

    assert result.fraud_score is None
    assert result.risk_level is None
    assert result.confidence < Decimal("1")
    assert any(
        code.startswith("FRAUD_DATA_")
        for code in result.reason_codes
    )


def test_missing_fraud_inputs_request_review():
    borrower = Borrower360(
        customer_id="FRAUD-MISSING-TEST",
        device_behaviour=DeviceBehaviourData(
            device="SYNTHETIC-DEVICE",
        ),
    )

    result = FraudValidator().validate(borrower)

    assert result.status == "REFER"
    assert any(
        code.startswith("FRAUD_DATA_")
        for code in result.reason_codes
    )


def test_incomplete_fraud_assessment_prevents_approval():
    orchestrator = DecisionOrchestrator()

    risk = make_risk_result(
        fraud_score=None,
        fraud_risk_level=None,
        fraud_confidence=Decimal("0.5"),
        fraud_reason_codes=["FRAUD_DATA_DOCUMENT_ANOMALY"],
    )

    result = orchestrator.decide(
        application_id="FRAUD-DECISION-001",
        policy_result=make_policy("APPROVE"),
        risk_result=risk,
    )

    assert result.decision == "REFER"
    assert "FRAUD_ASSESSMENT_INCOMPLETE" in result.reason_codes


def test_complete_clean_fraud_assessment_can_preserve_approval():
    orchestrator = DecisionOrchestrator()

    risk = make_risk_result(
        fraud_score=Decimal("0"),
        fraud_risk_level="VERY_LOW",
        fraud_confidence=Decimal("1"),
    )

    result = orchestrator.decide(
        application_id="FRAUD-DECISION-002",
        policy_result=make_policy("APPROVE"),
        risk_result=risk,
    )

    assert result.decision == "APPROVE"


def test_detected_fraud_finding_requests_review():
    orchestrator = DecisionOrchestrator()

    risk = make_risk_result(
        fraud_score=Decimal("25"),
        fraud_risk_level="LOW",
        fraud_confidence=Decimal("1"),
        fraud_reason_codes=["FRAUD_MULTIPLE_DEVICE"],
    )

    result = orchestrator.decide(
        application_id="FRAUD-DECISION-003",
        policy_result=make_policy("APPROVE"),
        risk_result=risk,
    )

    assert result.decision == "REFER"
    assert "FRAUD_RISK_REVIEW_REQUIRED" in result.reason_codes


def test_policy_rejection_is_not_overridden_by_fraud_review():
    orchestrator = DecisionOrchestrator()

    risk = make_risk_result(
        fraud_score=None,
        fraud_risk_level=None,
        fraud_confidence=Decimal("0"),
        fraud_reason_codes=["FRAUD_DATA_DEVICE"],
    )

    result = orchestrator.decide(
        application_id="FRAUD-DECISION-004",
        policy_result=make_policy("REJECT"),
        risk_result=risk,
    )

    assert result.decision == "REJECT"