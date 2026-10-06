from pathlib import Path

import joblib

from backend.app.database import SessionLocal
from backend.app.schemas.model_metadata import ModelMetadata
from backend.app.services.model_registry_service import (
    model_registry_service,
)


class CreditRiskModelLoader:

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parents[3]

        self.default_model_path = (
            self.base_dir
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
            environment="development",
        )

    def _resolve_model_path(
        self,
        model_reference: str,
    ) -> Path:

        reference_path = Path(model_reference)

        if reference_path.is_absolute():
            return reference_path

        return self.base_dir / reference_path

    def _load_default_model(self):

        if not self.default_model_path.exists():
            raise FileNotFoundError(
                f"Credit risk model not found: "
                f"{self.default_model_path}"
            )

        self.model = joblib.load(
            self.default_model_path
        )

        return self.model

    def _load_registered_model(
        self,
        model_reference: str,
        model_name: str,
        model_version: str,
        model_type: str | None,
        training_data_version: str | None,
        environment: str | None,
    ):

        model_path = self._resolve_model_path(
            model_reference
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"Registered credit risk model not found: "
                f"{model_path}"
            )

        self.model = joblib.load(model_path)

        self.metadata = ModelMetadata(
            model_name=model_name,
            model_version=model_version,
            model_type=model_type,
            training_data_version=training_data_version,
            environment=environment,
        )

        return self.model

    def load_governed(self):

        if self.model is not None:
            return self.model

        db = SessionLocal()

        try:
            active_model = (
                model_registry_service.get_active_model(
                    db=db,
                    model_name="credit_risk",
                    environment="development",
                )
            )
        except Exception:
            active_model = None
        finally:
            db.close()

        if active_model is not None:

            if not active_model.model_reference:
                raise ValueError(
                    "ACTIVE_MODEL_REFERENCE_MISSING"
                )

            return self._load_registered_model(
                model_reference=active_model.model_reference,
                model_name=active_model.model_name,
                model_version=active_model.model_version,
                model_type=active_model.model_type,
                training_data_version=(
                    active_model.training_data_version
                ),
                environment=active_model.environment,
            )

        # Development fallback.
        return self._load_default_model()

    def load(self):

        return self.load_governed()

    def get_metadata(self) -> ModelMetadata:

        return self.metadata


credit_risk_model_loader = CreditRiskModelLoader()