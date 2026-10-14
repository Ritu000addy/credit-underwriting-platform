from backend.app.schemas.fraud_features import FraudFeatures
from backend.app.schemas.fraud_rule import FraudRuleResult


class FraudRulesEngine:

    @staticmethod
    def _append_binary_rule(
        results: list[FraudRuleResult],
        *,
        available: int | None,
        unavailable_rule_id: str,
        rule_id: str,
        signal: int | None,
        unavailable_reason: str,
        not_evaluated_reason: str,
        fail_reason: str,
        pass_reason: str,
    ) -> None:
        if available != 1:
            results.append(
                FraudRuleResult(
                    rule_id=unavailable_rule_id,
                    status="NOT_EVALUATED",
                    reason=unavailable_reason,
                )
            )
        elif signal is None:
            results.append(
                FraudRuleResult(
                    rule_id=rule_id,
                    status="NOT_EVALUATED",
                    reason=not_evaluated_reason,
                )
            )
        elif signal == 1:
            results.append(
                FraudRuleResult(
                    rule_id=rule_id,
                    status="FAIL",
                    reason=fail_reason,
                )
            )
        else:
            results.append(
                FraudRuleResult(
                    rule_id=rule_id,
                    status="PASS",
                    reason=pass_reason,
                )
            )

    def evaluate(
        self,
        features: FraudFeatures,
    ) -> list[FraudRuleResult]:

        results: list[FraudRuleResult] = []

        # Identity mismatch
        self._append_binary_rule(
            results,
            available=features.identity_data_available,
            unavailable_rule_id="IDENTITY_DATA",
            rule_id="IDENTITY_MISMATCH",
            signal=features.identity_mismatch_flag,
            unavailable_reason="Identity data not available",
            not_evaluated_reason=(
                "Identity mismatch detector or comparison evidence is unavailable"
            ),
            fail_reason="Identity mismatch detected",
            pass_reason="No identity mismatch detected",
        )


        # Multiple-device signal
        self._append_binary_rule(
            results,
            available=features.device_data_available,
            unavailable_rule_id="DEVICE",
            rule_id="MULTIPLE_DEVICE",
            signal=features.multiple_device_flag,
            unavailable_reason="Device information not available",
            not_evaluated_reason=(
                "Multiple-device signal is unavailable"
            ),
            fail_reason="Multiple devices detected",
            pass_reason="No multiple-device anomaly detected",
        )


        # Device application velocity
        if (
            features.device_data_available != 1
            or features.device_velocity is None
        ):
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
                    reason=(
                        "High application velocity detected against "
                        "the development threshold"
                    ),
                )
            )
        else:
            results.append(
                FraudRuleResult(
                    rule_id="DEVICE_VELOCITY",
                    status="PASS",
                    reason=(
                        "Device application velocity is within "
                        "the development threshold"
                    ),
                )
            )

        # Transaction anomaly
        self._append_binary_rule(
            results,
            available=features.transaction_data_available,
            unavailable_rule_id="TRANSACTION_DATA",
            rule_id="TRANSACTION_ANOMALY",
            signal=features.transaction_anomaly_flag,
            unavailable_reason="Transaction information not available",
            not_evaluated_reason=(
                "Transaction anomaly detector has not been implemented"
            ),
            fail_reason="Transaction anomaly detected",
            pass_reason="No transaction anomaly detected",
        )


        # Document anomaly
        self._append_binary_rule(
            results,
            available=features.document_data_available,
            unavailable_rule_id="DOCUMENT_DATA",
            rule_id="DOCUMENT_ANOMALY",
            signal=features.document_anomaly_flag,
            unavailable_reason="Document information not available",
            not_evaluated_reason=(
                "Document anomaly detector has not been implemented"
            ),
            fail_reason="Document anomaly detected",
            pass_reason="No document anomaly detected",
        )


        # Session and behavioural anomaly
        self._append_binary_rule(
            results,
            available=features.behavioural_data_available,
            unavailable_rule_id="SESSION_BEHAVIOUR",
            rule_id="SESSION_BEHAVIOUR",
            signal=features.session_anomaly_flag,
            unavailable_reason=(
                "Behavioural information not available"
            ),
            not_evaluated_reason=(
                "Session anomaly detector has not been implemented"
            ),
            fail_reason="Session behaviour anomaly detected",
            pass_reason="No session behaviour anomaly detected",
        )

        return results


fraud_rules_engine = FraudRulesEngine()