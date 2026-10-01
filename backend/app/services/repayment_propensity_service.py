from decimal import Decimal

from backend.app.schemas.risk_features import CreditRiskFeatures

class RepaymentPropensityService:
    def assess(
        self,
        features: CreditRiskFeatures,
    ) -> dict:

        score = None

        if (
            features.past_loan_count is not None
            and features.repayment_history_count is not None
            and features.internal_dpd_count is not None
            and features.collection_count is not None
        ):
            score = Decimal("100")

            # Repayment history coverage
            if features.repayment_history_coverage is not None:
                if features.repayment_history_coverage < Decimal("0.50"):
                    score -= Decimal("30")
                elif features.repayment_history_coverage < Decimal("1.00"):
                    score -= Decimal("15")

            # Internal DPD
            if features.internal_dpd_count > 0:
                score -= Decimal("25")

            # Collections
            if features.collection_count > 0:
                score -= Decimal("20")

            # Bureau DPD
            if features.dpd_present == 1:
                score -= Decimal("15")

            # Write-off
            if features.write_off_present == 1:
                score -= Decimal("25")

            # Bounce history
            if (
                features.bounce_count is not None
                and features.bounce_count > 0
            ):
                score -= Decimal("10")
            
            if score < Decimal("0"):
                score = Decimal("0")
        
        return {
            "repayment_propensity": score,
        }

repayment_propensity_service = RepaymentPropensityService()