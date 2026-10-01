from decimal import Decimal

from backend.app.services.emi_calculator import emi_calculator

class LoanAffordabilityService:

    def calculate(
        self,
        principal: Decimal,
        annual_interest_rate: Decimal,
        tenure_months: int,
        monthly_income: Decimal,
        existing_emi: Decimal = Decimal("0"),
    ) -> dict:

        if monthly_income <= 0:
            raise ValueError("Monthly income must be greater than zero")

        proposed_emi = emi_calculator.calculate_emi(
            principal=principal,
            annual_interest_rate=annual_interest_rate,
            tenure_months=tenure_months,
        )

        total_monthly_obligation = (
            existing_emi + proposed_emi
        )

        foir = (
            total_monthly_obligation / monthly_income
        ) * Decimal("100")

        return {
            "proposed_emi": proposed_emi,
            "existing_emi": existing_emi,
            "total_monthly_obligation": total_monthly_obligation,
            "foir": foir.quantize(Decimal("0.01"))
        }

    def calculate_max_affordable_emi(
        self,
        monthly_income: Decimal,
        existing_emi: Decimal,
        maximum_foir: Decimal,
    ) -> Decimal:

        if monthly_income <= 0:
            raise ValueError(
                "Monthly income must be greater than zero"
            )

        if existing_emi < 0:
            raise ValueError(
                "Existing EMI cannot be negative"
            )

        if maximum_foir < 0:
            raise ValueError(
                "Maximum FOIR cannot be negative"
            )

        maximum_total_obligation = (
            monthly_income * maximum_foir / Decimal("100")
        )

        maximum_affordable_emi = (
            maximum_total_obligation - existing_emi
        )

        if maximum_affordable_emi < 0:
            maximum_affordable_emi = Decimal("0")

        return maximum_affordable_emi.quantize(
            Decimal("0.01")
        )

    def calculate_max_affordable_amount(
        self,
        monthly_income: Decimal,
        existing_emi: Decimal,
        annual_interest_rate: Decimal,
        tenure_months: int,
        maximum_foir: Decimal,
    ) -> Decimal:

        maximum_affordable_emi = (
            self.calculate_max_affordable_emi(
                monthly_income=monthly_income,
                existing_emi=existing_emi,
                maximum_foir=maximum_foir,
            )
        )

        if maximum_affordable_emi <= 0:
            return Decimal("0.00")

        maximum_affordable_amount = (
            emi_calculator.calculate_principal_from_emi(
                emi=maximum_affordable_emi,
                annual_interest_rate=annual_interest_rate,
                tenure_months=tenure_months,
            )
        )

        return maximum_affordable_amount
        
loan_affordability_service = LoanAffordabilityService()