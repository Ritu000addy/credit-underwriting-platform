from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.schemas.credit_decision import CreditDecisionOutput
from backend.app.services.credit_decision_service import credit_decision_service


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
)


db = SessionLocal()

try:
    result = credit_decision_service.save_decision(
        db=db,
        decision=decision,
    )

    print("DECISION SAVED")
    print("decision_id:", result.decision_id)
    print("application_id:", result.application_id)
    print("credit_score:", result.credit_score)
    print("risk_grade:", result.risk_grade)
    print("probability_of_default:", result.probability_of_default)
    print("risk_segment:", result.risk_segment)
    print("recommended_amount:", result.recommended_amount)
    print("recommended_tenure:", result.recommended_tenure)
    print("recommended_emi:", result.recommended_emi)
    print("foir:", result.foir)
    print("decision:", result.decision)
    print("reason_codes:", result.reason_codes)
    print("model_version:", result.model_version)
    print("policy_version:", result.policy_version)

finally:
    db.close()