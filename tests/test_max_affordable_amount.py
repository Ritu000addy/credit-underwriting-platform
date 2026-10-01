from decimal import Decimal

from backend.app.services.loan_affordability_service import (
    loan_affordability_service,
)


amount = (
    loan_affordability_service.calculate_max_affordable_amount(
        monthly_income=Decimal("80000"),
        existing_emi=Decimal("18000"),
        annual_interest_rate=Decimal("12"),
        tenure_months=36,
        maximum_foir=Decimal("50"),
    )
)

print("\n========== MAX AFFORDABLE AMOUNT ==========")
print("Maximum affordable amount:", amount)
print("===========================================")