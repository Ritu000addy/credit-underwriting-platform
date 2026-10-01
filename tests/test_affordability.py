from backend.app.schemas.risk_features import CreditRiskFeatures
from backend.app.services.affordability_service import affordability_service


features = CreditRiskFeatures(
    monthly_salary=80000,
    existing_emi=18000,
)

existing_ratio = (
    affordability_service.calculate_existing_obligation_ratio(
        features
    )
)

affordability_score = (
    affordability_service.calculate_affordability_score(
        features
    )
)

print("\n========== AFFORDABILITY RESULT ==========")
print("Existing obligation ratio:", existing_ratio)
print("Affordability score:", affordability_score)
print("==========================================")