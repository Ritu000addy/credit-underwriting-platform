from decimal import Decimal

from backend.app.schemas.risk_features import CreditRiskFeatures


class AffordabilityService:

    def calculate_existing_obligation_ratio(
        self,
        features: CreditRiskFeatures,
    ) -> Decimal | None:

        if (
            features.monthly_salary is None
            or features.monthly_salary <= 0
            or features.existing_emi is None
        ):
            return None

        ratio = (
            Decimal(str(features.existing_emi))
            / Decimal(str(features.monthly_salary))
        ) * Decimal("100")

        return ratio

    def calculate_affordability_score(
        self,
        features: CreditRiskFeatures,
    ) -> Decimal | None:

        existing_obligation_ratio = (
            self.calculate_existing_obligation_ratio(features)
        )

        if existing_obligation_ratio is None:
            return None

        # Development scoring only.
        # These bands are temporary and are NOT company policy.

        if existing_obligation_ratio <= Decimal("20"):
            score = Decimal("90")

        elif existing_obligation_ratio <= Decimal("30"):
            score = Decimal("75")

        elif existing_obligation_ratio <= Decimal("40"):
            score = Decimal("60")

        elif existing_obligation_ratio <= Decimal("50"):
            score = Decimal("40")

        else:
            score = Decimal("20")

        return score


affordability_service = AffordabilityService()