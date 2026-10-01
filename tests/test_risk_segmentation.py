from decimal import Decimal

from backend.app.services.risk_segmentation_service import (
    risk_segmentation_service,
)


# Test 1 — Low risk
low_risk = risk_segmentation_service.segment(
    probability_of_default=Decimal("0.01668"),
    credit_score=742,
    fraud_risk_level="VERY_LOW",
    repayment_propensity=Decimal("100"),
)

print("LOW RISK:", low_risk.model_dump())


# Test 2 — Medium risk
medium_risk = risk_segmentation_service.segment(
    probability_of_default=Decimal("0.05"),
    credit_score=680,
    fraud_risk_level="LOW",
    repayment_propensity=Decimal("70"),
)

print("MEDIUM RISK:", medium_risk.model_dump())


# Test 3 — High risk
high_risk = risk_segmentation_service.segment(
    probability_of_default=Decimal("0.15"),
    credit_score=580,
    fraud_risk_level="HIGH",
    repayment_propensity=Decimal("30"),
)

print("HIGH RISK:", high_risk.model_dump())


# Test 4 — Missing data
missing_data = risk_segmentation_service.segment(
    probability_of_default=None,
    credit_score=742,
    fraud_risk_level="VERY_LOW",
    repayment_propensity=Decimal("100"),
)

print("MISSING DATA:", missing_data.model_dump())