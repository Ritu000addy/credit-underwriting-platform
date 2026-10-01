from decimal import Decimal

class EMICalculator:

    def calculate_emi(
        self,
        principal: Decimal,
        annual_interest_rate: Decimal,
        tenure_months: int,
    ) -> Decimal:

        if principal <=0:
            raise ValueError("Principal must be greater than zero")
        
        if annual_interest_rate <0:
            raise ValueError("Interest rate cannot be negative")

        if tenure_months <=0:
            raise ValueError("Tenure must be greater than zero")

        monthly_rate = (
            annual_interest_rate / Decimal("100")
        ) / Decimal("12")

        # Zero-interest case
        if monthly_rate == 0:
            return (
                principal / Decimal(str(tenure_months))
            ).quantize(Decimal("0.01"))
        
        # Normal EMI calculation using the formula
        emi = (
            principal 
            * monthly_rate 
            * (1 + monthly_rate) ** tenure_months
            /
            ((1 + monthly_rate) ** tenure_months - 1)
        )

        return emi.quantize(Decimal("0.01"))

    def calculate_principal_from_emi(
        self,
        emi: Decimal,
        annual_interest_rate: Decimal,
        tenure_months: int,
    ) -> Decimal:

        if emi <= 0:
            raise ValueError(
                "EMI must be greater than zero"
            )

        if annual_interest_rate < 0:
            raise ValueError(
                "Interest rate cannot be negative"
            )

        if tenure_months <= 0:
            raise ValueError(
                "Tenure must be greater than zero"
            )

        monthly_rate = (
            annual_interest_rate / Decimal("100")
        ) / Decimal("12")

        # Zero-interest case
        if monthly_rate == 0:
            return (
                emi * Decimal(str(tenure_months))
            ).quantize(Decimal("0.01"))

        growth_factor = (
            (1 + monthly_rate) ** tenure_months
        )

        principal = (
            emi
            * (growth_factor - 1)
            / (monthly_rate * growth_factor)
        )

        return principal.quantize(
            Decimal("0.01")
        )

emi_calculator = EMICalculator()