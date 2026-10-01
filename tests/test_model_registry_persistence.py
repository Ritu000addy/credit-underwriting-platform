from decimal import Decimal

from backend.app.database import SessionLocal
from backend.app.services.model_registry_service import (
    model_registry_service,
)


db = SessionLocal()

try:
    result = model_registry_service.register_model(
        db=db,
        model_registry_id="DEV-MODEL-001",
        model_name="credit_risk",
        model_version="DEV-SYNTHETIC-LOGREG-01",
        model_type="LogisticRegression",
        training_data_version="SYNTHETIC-001",
        roc_auc=None,
        model_metrics="Development synthetic model. Metrics not production-valid.",
        deployment_status="DEVELOPMENT",
        environment="development",
        model_reference="data/synthetic/models/credit_risk_model.joblib",
    )

    print("MODEL REGISTERED")
    print("model_registry_id:", result.model_registry_id)
    print("model_name:", result.model_name)
    print("model_version:", result.model_version)
    print("model_type:", result.model_type)
    print("training_data_version:", result.training_data_version)
    print("deployment_status:", result.deployment_status)
    print("environment:", result.environment)
    print("model_reference:", result.model_reference)

finally:
    db.close()