from backend.app.schemas.fraud_features import FraudFeatures
from backend.app.schemas.fraud_rule import FraudRuleResult


class FraudRulesEngine:

    def evaluate(
        self,
        features: FraudFeatures,
    ) -> list[FraudRuleResult]:

        results: list[FraudRuleResult] = []

        # --------------------------------------------------
        # IDENTITY
        # --------------------------------------------------

        if features.identity_data_available != 1:

            results.append(
                FraudRuleResult(
                    rule_id="IDENTITY_DATA",
                    status="NOT_EVALUATED",
                    reason="Identity data not available",
                )
            )

        elif features.identity_mismatch_flag == 1:

            results.append(
                FraudRuleResult(
                    rule_id="IDENTITY_MISMATCH",
                    status="FAIL",
                    reason="Identity mismatch detected",
                )
            )

        else:

            results.append(
                FraudRuleResult(
                    rule_id="IDENTITY_MISMATCH",
                    status="PASS",
                    reason="No identity mismatch detected",
                )
            )

        # --------------------------------------------------
        # MULTIPLE DEVICE
        # --------------------------------------------------

        if features.device_data_available != 1:

            results.append(
                FraudRuleResult(
                    rule_id="DEVICE",
                    status="NOT_EVALUATED",
                    reason="Device information not available",
                )
            )

        elif features.multiple_device_flag == 1:

            results.append(
                FraudRuleResult(
                    rule_id="MULTIPLE_DEVICE",
                    status="FAIL",
                    reason="Multiple devices detected",
                )
            )

        else:

            results.append(
                FraudRuleResult(
                    rule_id="MULTIPLE_DEVICE",
                    status="PASS",
                    reason="No multiple-device anomaly detected",
                )
            )

        # --------------------------------------------------
        # DEVICE VELOCITY
        # --------------------------------------------------

        if features.device_velocity is None:

            results.append(
                FraudRuleResult(
                    rule_id="DEVICE_VELOCITY",
                    status="NOT_EVALUATED",
                    reason="Device velocity information not available",
                )
            )

        elif features.device_velocity > 5:

            results.append(
                FraudRuleResult(
                    rule_id="DEVICE_VELOCITY",
                    status="FAIL",
                    reason="High application velocity detected",
                )
            )

        else:

            results.append(
                FraudRuleResult(
                    rule_id="DEVICE_VELOCITY",
                    status="PASS",
                    reason="Device application velocity is within development threshold",
                )
            )

        # --------------------------------------------------
        # TRANSACTION
        # --------------------------------------------------

        if features.transaction_data_available != 1:

            results.append(
                FraudRuleResult(
                    rule_id="TRANSACTION_DATA",
                    status="NOT_EVALUATED",
                    reason="Transaction information not available",
                )
            )

        elif features.transaction_anomaly_flag == 1:

            results.append(
                FraudRuleResult(
                    rule_id="TRANSACTION_ANOMALY",
                    status="FAIL",
                    reason="Transaction anomaly detected",
                )
            )

        else:

            results.append(
                FraudRuleResult(
                    rule_id="TRANSACTION_ANOMALY",
                    status="PASS",
                    reason="No transaction anomaly detected",
                )
            )

        # --------------------------------------------------
        # DOCUMENT
        # --------------------------------------------------

        if features.document_data_available != 1:

            results.append(
                FraudRuleResult(
                    rule_id="DOCUMENT_DATA",
                    status="NOT_EVALUATED",
                    reason="Document information not available",
                )
            )

        elif features.document_anomaly_flag == 1:

            results.append(
                FraudRuleResult(
                    rule_id="DOCUMENT_ANOMALY",
                    status="FAIL",
                    reason="Document anomaly detected",
                )
            )

        else:

            results.append(
                FraudRuleResult(
                    rule_id="DOCUMENT_ANOMALY",
                    status="PASS",
                    reason="No document anomaly detected",
                )
            )

        # --------------------------------------------------
        # SESSION / BEHAVIOUR
        # --------------------------------------------------

        if features.behavioural_data_available != 1:

            results.append(
                FraudRuleResult(
                    rule_id="SESSION_BEHAVIOUR",
                    status="NOT_EVALUATED",
                    reason="Behavioural information not available",
                )
            )

        elif features.session_anomaly_flag == 1:

            results.append(
                FraudRuleResult(
                    rule_id="SESSION_BEHAVIOUR",
                    status="FAIL",
                    reason="Session behaviour anomaly detected",
                )
            )

        else:

            results.append(
                FraudRuleResult(
                    rule_id="SESSION_BEHAVIOUR",
                    status="PASS",
                    reason="No session behaviour anomaly detected",
                )
            )

        return results


fraud_rules_engine = FraudRulesEngine()