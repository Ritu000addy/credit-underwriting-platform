from decimal import Decimal

from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.risk_assessment import RiskAssessmentResult
from backend.app.services.feature_engineering import (
    feature_engineering_service,
)
from backend.app.services.affordability_service import (
    affordability_service,
)
from backend.app.services.loan_affordability_service import (
    loan_affordability_service,
)

from backend.app.services.income_stability_service import (
    income_stability_service,
)

from backend.app.services.repayment_propensity_service import (
    repayment_propensity_service,
)

from backend.app.services.credit_risk_service import (
    credit_risk_service,
)

from backend.app.services.fraud_risk_service import (
    fraud_risk_service,
)

from backend.app.services.risk_segmentation_service import (
    risk_segmentation_service,
)

from backend.app.services.reason_code_service import (
    reason_code_service,
)

class RiskAssessmentService:

    def assess(
        self,
        application: ApplicationCreate,
        borrower: Borrower360,
        annual_interest_rate: Decimal | None = None,
    ) -> RiskAssessmentResult:

        features = feature_engineering_service.build_credit_features(
            borrower = borrower,
        )

        income_stability_result = income_stability_service.assess(
            features
        )

        repayment_propensity_result = repayment_propensity_service.assess(
            features
        )

        credit_risk_result = credit_risk_service.assess(
            features
        )

        fraud_risk_result = fraud_risk_service.assess(
            borrower
        )

        existing_obligation_ratio = (
            affordability_service.calculate_existing_obligation_ratio(
            features
            )
        )

        affordability_score = (
            affordability_service.calculate_affordability_score(
                features
            )
        )

        recommended_amount = None
        recommended_tenure = None
        risk_segment = None

        proposed_emi = None
        foir = None

        if (
            annual_interest_rate is not None
            and features.monthly_salary is not None
            and features.existing_emi is not None
        ):

            affordability_result = (
                loan_affordability_service.calculate(
                    principal=Decimal(str(application.requested_amount)),
                    annual_interest_rate=Decimal(str(annual_interest_rate)),
                    tenure_months=application.loan_tenure_months,
                    monthly_income=Decimal(
                        str(features.monthly_salary)
                    ),
                    existing_emi=Decimal(
                        str(features.existing_emi)
                    ),
                )
            )

            proposed_emi = affordability_result["proposed_emi"]
            foir = affordability_result["foir"]

            maximum_affordable_amount = (
                loan_affordability_service.calculate_max_affordable_amount(
                    monthly_income=Decimal(
                        str(features.monthly_salary)
                    ),
                    existing_emi=Decimal(
                        str(features.existing_emi)
                    ),
                    annual_interest_rate=Decimal(
                        str(annual_interest_rate)
                    ),
                    tenure_months=application.loan_tenure_months,
                    maximum_foir=Decimal("50"),
                )
            )

            recommended_amount = min(
                Decimal(str(application.requested_amount)),
                maximum_affordable_amount,
            )

            recommended_tenure = application.loan_tenure_months
        
        segmentation_result = risk_segmentation_service.segment(
            probability_of_default=credit_risk_result[
                "model_output"
            ].probability_of_default,
            credit_score=credit_risk_result[
                "model_output"
            ].credit_score,
            fraud_risk_level=fraud_risk_result.risk_level,
            repayment_propensity=repayment_propensity_result[
                "repayment_propensity"
            ],
        )

        risk_segment = segmentation_result.risk_segment
        
        return RiskAssessmentResult(
            status="PENDING",

            # Core Risk Outputs
            credit_score=credit_risk_result[
                "model_output"
            ].credit_score,

            risk_grade=credit_risk_result[
                "model_output"
            ].risk_grade,

            probability_of_default=credit_risk_result[
                "model_output"
            ].probability_of_default,

            # Affordability / Repayment
            affordability_score=affordability_score,
            existing_obligation_ratio=existing_obligation_ratio,
            repayment_propensity=repayment_propensity_result[
                "repayment_propensity"
            ],

            # Fraud / Income
            fraud_score=fraud_risk_result.fraud_score,
            fraud_risk_level=fraud_risk_result.risk_level,
            fraud_confidence=fraud_risk_result.confidence,
            fraud_reason_codes=fraud_risk_result.reason_codes,

            income_stability_score=income_stability_result[
                "income_stability_score"
            ],
            
            income_trend=income_stability_result[
                "income_trend"
            ],

            # Loan Recommendation
            recommended_amount=recommended_amount,
            recommended_tenure=recommended_tenure,
            recommended_emi=proposed_emi,

            # Affordability
            foir=foir,

            # Risk Segmentation
            risk_segment=risk_segment,

            # Confidence
            confidence=credit_risk_result[
                "model_output"
            ].confidence,

            # Explainability
            reason_codes=[],

            # Model Governance
            model_version=credit_risk_result[
                "model_output"
            ].model_version,
        )

risk_assessment_service = RiskAssessmentService()