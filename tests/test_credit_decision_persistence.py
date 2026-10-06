from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.schemas.credit_decision import CreditDecisionOutput
from backend.app.services.credit_decision_service import credit_decision_service


def test_credit_decision_persistence():
    decision = CreditDecisionOutput(
        application_id="PERSIST-TEST-001",
        credit_score=742,
        risk_grade="B",
        probability_of_default=Decimal("0.01668"),
        affordability_score=Decimal("75"),
        repayment_propensity=Decimal("100"),
        fraud_score=Decimal("0"),
        income_stability_score=Decimal("80"),
        risk_segment="LOW_RISK",
        recommended_amount=Decimal("150000"),
        recommended_tenure=12,
        recommended_emi=Decimal("13328.81"),
        foir=Decimal("38.5"),
        decision="REFER",
        confidence=None,
        reason_codes=[
            "BUREAU_SCORE_ACCEPTABLE",
            "LOW_PROBABILITY_OF_DEFAULT",
            "FOIR_WITHIN_LIMIT",
            "LOW_FRAUD_RISK",
            "POLICY_DATA_INCOMPLETE",
        ],
        model_version="DEV-SYNTHETIC-LOGREG-01",
        policy_version="POL-DEV-01",
        effective_from="2026-09-01T00:00:00",
    )

    db = SessionLocal()

    try:
        result = credit_decision_service.save_decision(
            db=db,
            decision=decision,
        )

        assert result.decision_id is not None
        assert result.application_id == "PERSIST-TEST-001"
        assert result.credit_score == 742
        assert result.risk_grade == "B"
        assert result.probability_of_default == Decimal("0.01668")
        assert result.affordability_score == Decimal("75")
        assert result.repayment_propensity == Decimal("100")
        assert result.fraud_score == Decimal("0")
        assert result.income_stability_score == Decimal("80")
        assert result.risk_segment == "LOW_RISK"
        assert result.recommended_amount == Decimal("150000")
        assert result.recommended_tenure == 12
        assert result.recommended_emi == Decimal("13328.81")
        assert result.foir == Decimal("38.5")
        assert result.decision == "REFER"
        assert result.confidence is None
        assert result.reason_codes.split(",") == decision.reason_codes
        assert result.model_version == "DEV-SYNTHETIC-LOGREG-01"
        assert result.policy_version == "POL-DEV-01"
        assert result.effective_from == "2026-09-01T00:00:00"

    finally:
        db.close()