from backend.app.schemas.fraud_detection import FraudDetectionResult
from backend.app.schemas.fraud_features import FraudFeatures
from backend.app.services.fraud_policy_config import (
    FRAUD_POLICY_CONFIG,
)
from backend.app.services.fraud_rules_engine import (
    fraud_rules_engine,
)

class FraudDetectionService:

    def detect(
        self, 
        features: FraudFeatures
    ) -> FraudDetectionResult:

        # Evaluate configured fraud rules
        rule_results = fraud_rules_engine.evaluate(
            features
        )
        checks = [
            {
                "check_id": rule.rule_id,
                "status": rule.status,
                "reason": rule.reason,
            }
            for rule in rule_results
        ]

        if not checks:
            domains = [
                ("IDENTITY", "identity", features.identity_data_available),
                ("DEVICE", "device", features.device_data_available),
                ("TRANSACTION", "transaction", features.transaction_data_available,),
                ("DOCUMENT", "document", features.document_data_available),
                ("BEHAVIOUR", "behaviour", features.behavioural_data_available,),
            ]
        
            for check_id, config_key, data_available in domains:
                if data_available == 1:
                    if FRAUD_POLICY_CONFIG[config_key]["enabled"]:
                        status="PENDING"
                        reason= (
                            f"{check_id.title()} fraud rules are not enabled but not implemented yet"
                        )
                    else:
                        status="NOT_EVALUATED"
                        reason= (
                            f"{check_id.title()} fraud rules are not configured"
                        )
                else:
                    status="NOT_AVAILABLE"
                    reason= (
                        f"{check_id.title()} data is not available"
                    )

                checks.append(
                    {
                        "check_id": check_id,
                        "status": status,
                        "reason": reason,
                    }
                )

        result = FraudDetectionResult(
            status="PENDING",
            checks=checks,
            reason_codes=[],
        )      

        return result

fraud_detection_service = FraudDetectionService()