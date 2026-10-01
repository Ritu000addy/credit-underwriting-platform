from decimal import Decimal

from backend.app.schemas.reason_codes import ReasonCodeResult


class ReasonCodeService:

    def generate(
        self,
        credit_score: int | None,
        probability_of_default: Decimal | None,
        affordability_score: Decimal | None,
        repayment_propensity: Decimal | None,
        fraud_risk_level: str | None,
        income_stability_score: Decimal | None,
        foir: Decimal | None,
        policy_status: str | None,
        policy_not_evaluated_count: int = 0,
    ) -> ReasonCodeResult:

        reason_codes: list[str] = []

        # --------------------------------------------------
        # Credit Risk
        # --------------------------------------------------

        if credit_score is not None:
            if credit_score >= 700:
                reason_codes.append("BUREAU_SCORE_ACCEPTABLE")
            elif credit_score < 650:
                reason_codes.append("BUREAU_SCORE_LOW")

        if probability_of_default is not None:
            if probability_of_default <= Decimal("0.03"):
                reason_codes.append("LOW_PROBABILITY_OF_DEFAULT")
            elif probability_of_default > Decimal("0.08"):
                reason_codes.append("HIGH_PROBABILITY_OF_DEFAULT")

        # --------------------------------------------------
        # Affordability
        # --------------------------------------------------

        if affordability_score is not None:
            if affordability_score >= Decimal("75"):
                reason_codes.append("AFFORDABILITY_ACCEPTABLE")
            elif affordability_score < Decimal("50"):
                reason_codes.append("AFFORDABILITY_CONCERN")

        if foir is not None:
            if foir <= Decimal("50"):
                reason_codes.append("FOIR_WITHIN_LIMIT")
            else:
                reason_codes.append("FOIR_ABOVE_LIMIT")

        # --------------------------------------------------
        # Repayment
        # --------------------------------------------------

        if repayment_propensity is not None:
            if repayment_propensity >= Decimal("80"):
                reason_codes.append("STRONG_REPAYMENT_HISTORY")
            elif repayment_propensity < Decimal("50"):
                reason_codes.append("WEAK_REPAYMENT_HISTORY")

        # --------------------------------------------------
        # Fraud
        # --------------------------------------------------

        if fraud_risk_level == "VERY_LOW":
            reason_codes.append("LOW_FRAUD_RISK")
        elif fraud_risk_level == "HIGH":
            reason_codes.append("HIGH_FRAUD_RISK")

        # --------------------------------------------------
        # Income Stability
        # --------------------------------------------------

        if income_stability_score is not None:
            if income_stability_score >= Decimal("75"):
                reason_codes.append("STABLE_INCOME")
            elif income_stability_score < Decimal("50"):
                reason_codes.append("INCOME_STABILITY_CONCERN")

        # --------------------------------------------------
        # Policy / Data Completeness
        # --------------------------------------------------

        if policy_status == "REJECT":
            reason_codes.append("POLICY_RULE_FAILURE")

        if policy_not_evaluated_count > 0:
            reason_codes.append("POLICY_DATA_INCOMPLETE")

        return ReasonCodeResult(
            reason_codes=reason_codes
        )


reason_code_service = ReasonCodeService()