from decimal import Decimal

from backend.app.schemas.risk_segmentation import RiskSegmentationResult


class RiskSegmentationService:

    def segment(
        self,
        probability_of_default: Decimal | None,
        credit_score: int | None,
        fraud_risk_level: str | None,
        repayment_propensity: Decimal | None,
    ) -> RiskSegmentationResult:

        if (
            probability_of_default is None
            or credit_score is None
            or fraud_risk_level is None
            or repayment_propensity is None
        ):
            return RiskSegmentationResult(
                risk_segment=None
            )

        # Development segmentation only.
        # These thresholds are temporary and are NOT company policy.

        if (
            probability_of_default <= Decimal("0.03")
            and credit_score >= 700
            and fraud_risk_level == "VERY_LOW"
            and repayment_propensity >= Decimal("80")
        ):
            segment = "LOW_RISK"

        elif (
            probability_of_default <= Decimal("0.08")
            and credit_score >= 650
            and fraud_risk_level in ["VERY_LOW", "LOW", "MEDIUM"]
            and repayment_propensity >= Decimal("50")
        ):
            segment = "MEDIUM_RISK"

        else:
            segment = "HIGH_RISK"

        return RiskSegmentationResult(
            risk_segment=segment
        )


risk_segmentation_service = RiskSegmentationService()