from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.risk_features import CreditRiskFeatures

class FeatureEngineeringService:
    def build_credit_features(
        self,
        borrower: Borrower360,
    ) -> CreditRiskFeatures:

        bureau = borrower.credit_bureau
        internal_history = borrower.internal_history
        bank = borrower.bank_cash_flow
        employment = borrower.employment_business

        features = CreditRiskFeatures()

        features.proposed_emi = None

        # Credit Bureau Features
        if bureau is not None:
            features.bureau_score = bureau.score
            features.dpd = bureau.dpd

            if bureau.dpd is not None:
                features.dpd_present = int(bureau.dpd > 0)

            features.credit_enquiries = bureau.enquiries
            features.active_loans = bureau.active_loans

            if (
                bureau.enquiries is not None
                and bureau.active_loans is not None
                and bureau.active_loans > 0
            ):
                features.enquiries_to_active_loans_ratio = float(
                    bureau.enquiries / bureau.active_loans
                )

            if bureau.total_outstanding is not None:
                features.total_outstanding = float(
                    bureau.total_outstanding
                )

            if bureau.write_offs is not None:
                features.write_offs = float(
                    bureau.write_offs
                )
            
            if bureau.write_offs is not None:
                features.write_off_present = int(
                    bureau.write_offs > 0
                )

            if (
                bureau is not None
                and employment is not None
                and bureau.total_outstanding is not None
                and employment.salary is not None
                and employment.salary > 0
            ):
                annual_income = employment.salary * 12

                features.outstanding_to_annual_income_ratio = float(
                    bureau.total_outstanding / annual_income
                )

        # Internal History Features
        if internal_history is not None:
            features.past_loan_count = len(
                internal_history.past_loans
            )

            features.repayment_history_count = len(
                internal_history.repayment
            )

            if internal_history.past_loans and len(internal_history.past_loans) > 0:
                features.repayment_history_coverage = float(
                    len(internal_history.repayment) / len(internal_history.past_loans)
                )
            else:
                features.repayment_history_coverage = 0.0

            features.internal_dpd_count = len(
                internal_history.dpd
            )

            features.collection_count = len(
                internal_history.collections
            )

        # Bank / Cash Flow Features
        if bank is not None:
            if bank.credits is not None:
                features.monthly_credits = float(bank.credits)
            
            if bank.debits is not None:
                features.monthly_debits = float(bank.debits)

            if bank.credits is not None and bank.debits is not None:
                features.net_monthly_cash_flow = float(
                    bank.credits - bank.debits
                )

            if bank.balance is not None:
                features.bank_balance = float(bank.balance)

            if bank.emi is not None:
                features.existing_emi = float(bank.emi)
            
            if bank.bounce is not None:
                features.bounce_count = bank.bounce

            if bank.transaction_count is not None:
                features.transaction_count = bank.transaction_count
            
                if bank.transaction_count > 0 and bank.bounce is not None:
                    features.bounce_rate = float(
                        bank.bounce / bank.transaction_count
                    )

            if bank.income_pattern is not None:
                features.income_trend = bank.income_pattern.get(
                    "income_trend"
                )

        # Employment / Income

        if employment is not None:
            if employment.salary is not None:
                features.monthly_salary = float(
                    employment.salary
                )
            
            features.employer = employment.employer

        if (
            bank is not None
            and employment is not None
            and employment.salary is not None
            and employment.salary > 0
        ):
            if bank.emi is not None:
                features.emi_to_income_ratio = float(
                    bank.emi / employment.salary
                )
            if bank.credits is not None and bank.debits is not None:
                features.cash_flow_to_income_ratio = float(
                    (bank.credits - bank.debits) / employment.salary
                )
            if bank.debits is not None:
                features.expense_to_income_ratio = float(
                    bank.debits /employment.salary
                )

        return features

feature_engineering_service = FeatureEngineeringService()