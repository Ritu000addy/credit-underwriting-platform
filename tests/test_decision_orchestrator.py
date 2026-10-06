from decimal import Decimal

from backend.app.schemas.policy import (
    PolicyEvaluationResult,
    PolicyRuleResult,
)
from backend.app.schemas.risk_assessment import RiskAssessmentResult
from backend.app.services.decision_orchestrator import decision_orchestrator


def test_decision_orchestrator_refer_path():
    policy_result = PolicyEvaluationResult(
        policy_status="REFER",
        policy_version="POL-2026.09",
        effective_from="2026-09-01T00:00:00",
        effective_to=None,
        rules=[
            PolicyRuleResult(
                rule_id="AGE",
                status="NOT_EVALUATED",
                reason="Age policy parameters not configured",
            ),
            PolicyRuleResult(
                rule_id="BUREAU",
                status="NOT_EVALUATED",
                reason="Bureau policy parameters not configured",
            ),
        ],
    )

    risk_result = RiskAssessmentResult(
        status="PENDING",
        credit_score=742,
        risk_grade="B",
        probability_of_default=Decimal("0.034"),
        affordability_score=None,
        repayment_propensity=None,
        fraud_score=Decimal("8"),
        income_stability_score=None,
        income_trend="STABLE",
        recommended_amount=Decimal("150000"),
        recommended_tenure=12,
        recommended_emi=Decimal("14200"),
        foir=Decimal("38.5"),
        risk_segment=None,
        confidence=Decimal("0.91"),
        reason_codes=[
            "STABLE_INCOME",
            "LOW_RECENT_ENQUIRIES",
            "GOOD_REPAYMENT_HISTORY",
        ],
        model_version="CRD-ML-01.04",
    )

    result = decision_orchestrator.decide(
        application_id="LN102938",
        policy_result=policy_result,
        risk_result=risk_result,
    )

    assert result.application_id == "LN102938"
    assert result.decision == "REFER"
    assert result.policy_version == "POL-2026.09"
    assert result.effective_from == "2026-09-01T00:00:00"
    assert result.model_version == "CRD-ML-01.04"