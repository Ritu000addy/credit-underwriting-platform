from decimal import Decimal

from backend.app.services.emi_calculator import (
    emi_calculator,
)


principal = (
    emi_calculator.calculate_principal_from_emi(
        emi=Decimal("22000"),
        annual_interest_rate=Decimal("12"),
        tenure_months=36,
    )
)

emi_check = (
    emi_calculator.calculate_emi(
        principal=principal,
        annual_interest_rate=Decimal("12"),
        tenure_months=36,
    )
)

print("\n========== PRINCIPAL FROM EMI ==========")
print("Maximum affordable principal:", principal)
print("EMI verification:", emi_check)
print("========================================")