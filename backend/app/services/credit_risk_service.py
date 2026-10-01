from decimal import Decimal

import pandas as pd 

from backend.app.schemas.risk_features import CreditRiskFeatures

from backend.app.schemas.credit_risk import CreditRiskModelOutput

from backend.app.services.model_loader import (
    credit_risk_model_loader,
)

class CreditRiskService:

    def __init__(self):

        self.model = credit_risk_model_loader.load()
        self.metadata = credit_risk_model_loader.get_metadata()

    def build_model_features(
        self,
        features: CreditRiskFeatures,
    ) -> dict:

        return {
            # Credit Bureau
            "bureau_score": features.bureau_score,
            "dpd": features.dpd,
            "dpd_present": features.dpd_present,
            "credit_enquiries": features.credit_enquiries,
            "active_loans": features.active_loans,
            "total_outstanding": features.total_outstanding,
            # "write_offs": features.write_offs,
            # "write_off_present": features.write_off_present,
            "outstanding_to_annual_income_ratio": (
                features.outstanding_to_annual_income_ratio
            ),
            "enquiries_to_active_loans_ratio": (
                features.enquiries_to_active_loans_ratio
            ),

            # Internal History
            "past_loan_count": features.past_loan_count,
            "repayment_history_count": (
                features.repayment_history_count
            ),
            "repayment_history_coverage": (
                features.repayment_history_coverage
            ),
            "internal_dpd_count": features.internal_dpd_count,
            "collection_count": features.collection_count,

            # Bank /Cash Flow
            "monthly_credits": features.monthly_credits,
            "monthly_debits": features.monthly_debits,
            "net_monthly_cash_flow": (
                features.net_monthly_cash_flow
            ),
            "bank_balance": features.bank_balance,
            "existing_emi": features.existing_emi,
            "bounce_count": features.bounce_count,
            "transaction_count": features.transaction_count,
            "bounce_rate": features.bounce_rate,

            # Employment / Income
            "monthly_salary": features.monthly_salary,
            "emi_to_income_ratio": (
                features.emi_to_income_ratio
            ),
            "cash_flow_to_income_ratio": (
                features.cash_flow_to_income_ratio
            ),
            "expense_to_income_ratio": (
                features.expense_to_income_ratio
            ),
        }

    def calculate_risk_grade(
        self,
        bureau_score: int | None,
    ) -> str | None:

        if bureau_score is None:
            return None

        if bureau_score >= 750:
            return "A"

        if bureau_score >= 700:
            return "B"

        if bureau_score >= 650:
            return "C"

        if bureau_score >= 600:
            return "D"

        return "E"
        
    def assess(
        self,
        features: CreditRiskFeatures,
    ) -> dict:

        model_features = self.build_model_features(
            features
        )

        model_input = pd.DataFrame(
            [model_features]
        )

        expected_features = list(
            self.model.feature_names_in_
        )

        model_input = model_input.loc[:, expected_features]

        probability = self.model.predict_proba(
            model_input
        )[0][1]

        probability_of_default = Decimal(
            str(round(probability, 6))
        )

        credit_score = features.bureau_score

        risk_grade = self.calculate_risk_grade(
            credit_score
        )

        model_output = CreditRiskModelOutput(
            probability_of_default=probability_of_default,
            credit_score=credit_score,
            risk_grade=risk_grade,
            confidence=None,
            model_version=self.metadata.model_version,
        )

        return {
            "model_output": model_output,
            "model_features": model_features,
        }

credit_risk_service = CreditRiskService()