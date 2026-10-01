from backend.app.schemas.credit_decision import CreditDecisionOutput

decision = CreditDecisionOutput(
    application_id="LN102938",

    credit_score=742,
    risk_grade="B",
    probability_of_default=0.034,

    recommended_amount=150000,
    recommended_tenure=12,
    recommended_emi=14200,

    foir=38.5,
    fraud_score=8,

    decision="APPROVE",
    confidence=0.91,

    reason_codes=[
        "STABLE_INCOME",
        "LOW_RECENT_ENQUIRIES",
        "GOOD_REPAYMENT_HISTORY",        
    ],

    policy_checks=[],

    model_version="CRD-ML-01.04",
    policy_version="POL-2026-09",
)

print(decision.model_dump())