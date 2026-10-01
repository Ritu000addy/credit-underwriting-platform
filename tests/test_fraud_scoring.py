from backend.app.schemas.fraud_features import FraudFeatures
from backend.app.schemas.fraud_rule import FraudRuleResult
from backend.app.services.fraud_scoring_service import (
    fraud_scoring_service,
)


features = FraudFeatures()


# Clean rules
clean_rules = [
    FraudRuleResult(
        rule_id="IDENTITY_MISMATCH",
        status="PASS",
        reason="No identity mismatch detected",
    ),
    FraudRuleResult(
        rule_id="MULTIPLE_DEVICE",
        status="PASS",
        reason="No multiple-device anomaly detected",
    ),
    FraudRuleResult(
        rule_id="DEVICE_VELOCITY",
        status="PASS",
        reason="Device velocity within threshold",
    ),
    FraudRuleResult(
        rule_id="TRANSACTION_ANOMALY",
        status="PASS",
        reason="No transaction anomaly detected",
    ),
]


# Fraud rules with failures
fraud_rules = [
    FraudRuleResult(
        rule_id="IDENTITY_MISMATCH",
        status="FAIL",
        reason="Identity mismatch detected",
    ),
    FraudRuleResult(
        rule_id="MULTIPLE_DEVICE",
        status="FAIL",
        reason="Multiple devices detected",
    ),
    FraudRuleResult(
        rule_id="DEVICE_VELOCITY",
        status="PASS",
        reason="Device velocity within threshold",
    ),
    FraudRuleResult(
        rule_id="TRANSACTION_ANOMALY",
        status="NOT_EVALUATED",
        reason="Transaction data unavailable",
    ),
]


clean_result = fraud_scoring_service.calculate(
    features=features,
    rule_results=clean_rules,
)

fraud_result = fraud_scoring_service.calculate(
    features=features,
    rule_results=fraud_rules,
)


print("\n========== FRAUD SCORING ==========")

print("Clean case:")
print(clean_result.model_dump())

print("\nFraud case:")
print(fraud_result.model_dump())

print("===================================")