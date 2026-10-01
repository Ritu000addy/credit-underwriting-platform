from decimal import Decimal

from backend.app.services.loan_affordability_service import (
    loan_affordability_service,
)


maximum_emi = (
    loan_affordability_service.calculate_max_affordable_emi(
        monthly_income=Decimal("80000"),
        existing_emi=Decimal("18000"),
        maximum_foir=Decimal("50"),
    )
)

print("\n========== MAX AFFORDABLE EMI ==========")
print("Maximum affordable EMI:", maximum_emi)
print("========================================")