from decimal import Decimal

from backend.app.services.reason_code_service import (
    reason_code_service,
)


result = reason_code_service.generate(
    credit_score=742,
    probability_of_default=Decimal("0.01668"),
    affordability_score=Decimal("75"),
    repayment_propensity=Decimal("100"),
    fraud_risk_level="VERY_LOW",
    income_stability_score=Decimal("80"),
    foir=Decimal("43.26"),
    policy_status="REFER",
    policy_not_evaluated_count=3,
)

print(result.model_dump())