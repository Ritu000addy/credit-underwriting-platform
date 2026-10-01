from ast import Str
from decimal import Decimal

from backend.app.schemas.risk_features import CreditRiskFeatures

class IncomeStabilityService:

    def assess(
        self,
        features: CreditRiskFeatures,
    ) -> dict:

        score = None
        trend = features.income_trend

        if (
            features.monthly_credits is not None
            and features.monthly_debits is not None
            and features.monthly_credits > 0
        ):
            expense_ratio = (
                Decimal(str(features.monthly_debits))
                / Decimal(str(features.monthly_credits))
            )

            if expense_ratio <= Decimal("0.60"):
                score = Decimal("80")

            elif expense_ratio <= Decimal("0.80"):
                score = Decimal("60")

            else:
                score = Decimal("40")

        return {
            "income_stability_score": score,
            "income_trend": trend,
        }

income_stability_service = IncomeStabilityService()