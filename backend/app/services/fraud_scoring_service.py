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

        # --------------------------------------------------
        # Count rule outcomes
        # --------------------------------------------------

        fail_count = sum(
            1
            for rule in rule_results
            if rule.status == "FAIL"
        )

        pass_count = sum(
            1
            for rule in rule_results
            if rule.status == "PASS"
        )

        not_evaluated_count = sum(
            1
            for rule in rule_results
            if rule.status == "NOT_EVALUATED"
        )

        total_rules = len(rule_results)

        # --------------------------------------------------
        # Development fraud score
        #
        # 0   = lowest observed fraud risk
        # 100 = highest observed fraud risk
        # --------------------------------------------------

        if total_rules == 0:

            fraud_score = None
            risk_level = None
            confidence = None
            reason_codes = []

        else:

            # Each failed fraud rule contributes to the score.
            fraud_score = Decimal(
                str(
                    min(
                        100,
                        fail_count * 25,
                    )
                )
            )

            # --------------------------------------------------
            # Risk level
            # --------------------------------------------------

            if fraud_score >= 75:

                risk_level = "HIGH"

            elif fraud_score >= 50:

                risk_level = "MEDIUM"

            elif fraud_score >= 25:

                risk_level = "LOW"

            else:

                risk_level = "VERY_LOW"

            # --------------------------------------------------
            # Confidence
            # --------------------------------------------------

            evaluated_rules = (
                pass_count + fail_count
            )

            if evaluated_rules > 0:

                confidence = Decimal(
                    str(
                        round(
                            evaluated_rules / total_rules,
                            4,
                        )
                    )
                )

            else:

                confidence = Decimal("0")

            # --------------------------------------------------
            # Reason codes
            # --------------------------------------------------

            reason_codes = []

            for rule in rule_results:

                if rule.status == "FAIL":

                    reason_codes.append(
                        f"FRAUD_{rule.rule_id}"
                    )

                elif rule.status == "NOT_EVALUATED":

                    reason_codes.append(
                        f"FRAUD_DATA_{rule.rule_id}"
                    )

        return FraudScoreResult(
            fraud_score=fraud_score,
            risk_level=risk_level,
            confidence=confidence,
            reason_codes=reason_codes,
        )


fraud_scoring_service = FraudScoringService()