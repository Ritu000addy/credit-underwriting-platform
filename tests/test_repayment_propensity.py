from backend.app.schemas.risk_features import CreditRiskFeatures
from backend.app.services.repayment_propensity_service import (
    repayment_propensity_service,
)
from decimal import Decimal


# Clean repayment history
clean_features = CreditRiskFeatures(
    past_loan_count=1,
    repayment_history_count=1,
    repayment_history_coverage=Decimal("1.00"),
    internal_dpd_count=0,
    collection_count=0,
    dpd_present=0,
    write_off_present=0,
    bounce_count=0,
)

clean_result = repayment_propensity_service.assess(
    clean_features
)


# Adverse repayment history
adverse_features = CreditRiskFeatures(
    past_loan_count=2,
    repayment_history_count=2,
    repayment_history_coverage=Decimal("0.50"),
    internal_dpd_count=1,
    collection_count=1,
    dpd_present=1,
    write_off_present=1,
    bounce_count=2,
)

adverse_result = repayment_propensity_service.assess(
    adverse_features
)


print("\n========== REPAYMENT PROPENSITY ==========")

print(
    "Clean repayment score:",
    clean_result["repayment_propensity"],
)

print(
    "Adverse repayment score:",
    adverse_result["repayment_propensity"],
)

print("===========================================")