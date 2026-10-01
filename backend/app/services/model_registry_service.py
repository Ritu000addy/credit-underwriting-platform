from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.model_registry import ModelRegistry


class ModelRegistryService:

    def register_model(
        self,
        db: Session,
        model_registry_id: str,
        model_name: str,
        model_version: str,
        deployment_status: str,
        model_type: str | None = None,
        training_data_version: str | None = None,
        training_date: datetime | None = None,
        roc_auc: Decimal | None = None,
        model_metrics: str | None = None,
        environment: str | None = None,
        model_reference: str | None = None,
    ) -> ModelRegistry:

        model = ModelRegistry(
            model_registry_id=model_registry_id,
            model_name=model_name,
            model_version=model_version,
            model_type=model_type,
            training_data_version=training_data_version,
            training_date=training_date,
            roc_auc=roc_auc,
            model_metrics=model_metrics,
            deployment_status=deployment_status,
            environment=environment,
            model_reference=model_reference,
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        return model


model_registry_service = ModelRegistryService()