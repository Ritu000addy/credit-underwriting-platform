from pathlib import Path
import joblib

from backend.app.schemas.model_metadata import ModelMetadata

class CreditRiskModelLoader:

    def __init__(self):
        base_dir = Path(__file__).resolve().parents[3]

        self.model_path = (
            base_dir
            / "data"
            / "synthetic"
            / "models"
            / "credit_risk_model.joblib"
        )

        self.model = None

        self.metadata = ModelMetadata(
            model_name="credit_risk",
            model_version="DEV-SYNTHETIC-LOGREG-01",
            model_type="LogisticRegression",
            training_data_version="SYNTHETIC-001",
            environment="development"
        )

    def load(self):
        if self.model is None:
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Credit risk model not found: {self.model_path}"
                )

            self.model = joblib.load(
                self.model_path
            )

        return self.model

    def get_metadata(self) -> ModelMetadata:
        return self.metadata

credit_risk_model_loader = CreditRiskModelLoader()