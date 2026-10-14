from decimal import Decimal

from backend.app.schemas.fraud_features import FraudFeatures
from backend.app.schemas.fraud_rule import FraudRuleResult
from backend.app.schemas.fraud_score import FraudScoreResult


class FraudScoringService:

    def calculate(
        self,
        features: FraudFeatures,
        rule_results: list[FraudRuleResult],
    ) -> FraudScoreResult:

        del features  # The score is based on evaluated rule outcomes.

        # --------------------------------------------------
        # Count rule outcomes
        # --------------------------------------------------

        fail_count = sum(
            rule.status == "FAIL"
            for rule in rule_results
        )

        pass_count = sum(
            rule.status == "PASS"
            for rule in rule_results
        )

        incomplete_count = sum(
            rule.status in {"NOT_EVALUATED", "EXCEPTION"}
            for rule in rule_results
        )

        total_rules = len(rule_results)
        reason_codes: list[str] = []

        for rule in rule_results:
            if rule.status == "FAIL":
                reason_codes.append(f"FRAUD_{rule.rule_id}")
            elif rule.status in {"NOT_EVALUATED", "EXCEPTION"}:
                reason_codes.append(f"FRAUD_DATA_{rule.rule_id}")

        if total_rules == 0:
            return FraudScoreResult(
                fraud_score=None,
                risk_level=None,
                confidence=None,
                reason_codes=reason_codes,
            )

        evaluated_rules = pass_count + fail_count
        confidence = Decimal(
            str(round(evaluated_rules / total_rules, 4))
        )

        # No observed failures is not the same as a clean result
        # when one or more checks could not be evaluated.
        if fail_count == 0 and incomplete_count > 0:
            fraud_score = None
            risk_level = None
        else:
            fraud_score = Decimal(
                str(min(100, fail_count * 25))
            )

            if fraud_score >= 75:
                risk_level = "HIGH"
            elif fraud_score >= 50:
                risk_level = "MEDIUM"
            elif fraud_score >= 25:
                risk_level = "LOW"
            else:
                risk_level = "VERY_LOW"

        return FraudScoreResult(
            fraud_score=fraud_score,
            risk_level=risk_level,
            confidence=confidence,
            reason_codes=reason_codes,
        )


fraud_scoring_service = FraudScoringService()