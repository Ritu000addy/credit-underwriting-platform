from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.fraud_risk import FraudRiskResult
from backend.app.services.fraud_feature_engineering import (
    fraud_feature_engineering_service,
)
from backend.app.services.fraud_detection_service import (
    fraud_detection_service,
)
from backend.app.services.fraud_rules_engine import (
    fraud_rules_engine,
)
from backend.app.services.fraud_scoring_service import (
    fraud_scoring_service,
)

class FraudRiskService:

    def assess(
        self,
        borrower: Borrower360,
    ) -> FraudRiskResult:

        # Build fraud features
        features = fraud_feature_engineering_service.build_features(
            borrower
        )

        # Evaluate fraud rules
        rule_results = fraud_rules_engine.evaluate(
            features
        )

        # Calculate fraud score
        scoring_result = fraud_scoring_service.calculate(
            features=features,
            rule_results=rule_results,
        )

        return FraudRiskResult(
            fraud_score=scoring_result.fraud_score,
            risk_level=scoring_result.risk_level,
            confidence=scoring_result.confidence,
            reason_codes=scoring_result.reason_codes,
            model_version=None,
        )

fraud_risk_service = FraudRiskService()