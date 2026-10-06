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
        governance_notes: str | None = None,
    ) -> ModelRegistry:

        existing = (
            db.query(ModelRegistry)
            .filter(
                ModelRegistry.model_name == model_name,
                ModelRegistry.model_version == model_version,
            )
            .first()
        )

        if existing is not None:
            raise ValueError(
                "MODEL_VERSION_ALREADY_REGISTERED"
            )

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
            lifecycle_status="REGISTERED",
            validation_status="NOT_VALIDATED",
            environment=environment,
            model_reference=model_reference,
            governance_notes=governance_notes,
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        return model

    def get_model(
        self,
        db: Session,
        model_name: str,
        model_version: str,
    ) -> ModelRegistry | None:

        return (
            db.query(ModelRegistry)
            .filter(
                ModelRegistry.model_name == model_name,
                ModelRegistry.model_version == model_version,
            )
            .first()
        )

    def get_active_model(
        self,
        db: Session,
        model_name: str,
        environment: str | None = None,
    ) -> ModelRegistry | None:

        query = (
            db.query(ModelRegistry)
            .filter(
                ModelRegistry.model_name == model_name,
                ModelRegistry.lifecycle_status == "ACTIVE",
                ModelRegistry.validation_status == "PASSED",
            )
        )
        if environment is not None:
            query = query.filter(
                ModelRegistry.environment == environment
            )

        return (
            query
            .order_by(ModelRegistry.created_at.desc())
            .first()
        )

    def start_validation(
        self,
        db: Session,
        model: ModelRegistry,
    ) -> ModelRegistry:

        if model.lifecycle_status not in {
            "REGISTERED",
            "VALIDATION",
        }:
            raise ValueError(
                "MODEL_NOT_ELIGIBLE_FOR_VALIDATION"
            )

        model.lifecycle_status = "VALIDATION"
        model.validation_status = "IN_PROGRESS"

        db.commit()
        db.refresh(model)

        return model
        
    def complete_validation(
        self,
        db: Session,
        model: ModelRegistry,
        passed: bool,
        validated_by: str,
        validation_notes: str | None = None,
    ) -> ModelRegistry:

        if model.lifecycle_status != "VALIDATION":
            raise ValueError(
                "MODEL_NOT_IN_VALIDATION"
            )

        validated_by = validated_by.strip()

        if not validated_by:
            raise ValueError(
                "VALIDATED_BY_REQUIRED"
            )

        model.validation_status = (
            "PASSED" if passed else "FAILED"
        )
        model.validation_date = datetime.utcnow()
        model.validated_by = validated_by
        model.validation_notes = validation_notes

        if passed:
            model.lifecycle_status = "APPROVED"
        else:
            model.lifecycle_status = "REJECTED"

        db.commit()
        db.refresh(model)

        return model

    def approve_model(
        self,
        db: Session,
        model: ModelRegistry,
        approved_by: str,
    ) -> ModelRegistry:

        if model.validation_status != "PASSED":
            raise ValueError(
                "MODEL_VALIDATION_NOT_PASSED"
            )

        approved_by = approved_by.strip()

        if not approved_by:
            raise ValueError(
                "APPROVED_BY_REQUIRED"
            )

        model.lifecycle_status = "APPROVED"
        model.approval_date = datetime.utcnow()
        model.approved_by = approved_by

        db.commit()
        db.refresh(model)

        return model

    def activate_model(
        self,
        db: Session,
        model: ModelRegistry,
    ) -> ModelRegistry:

        if model.validation_status != "PASSED":
            raise ValueError(
                "MODEL_VALIDATION_NOT_PASSED"
            )

        if model.lifecycle_status != "APPROVED":
            raise ValueError(
                "MODEL_NOT_APPROVED"
            )

        active_models = (
            db.query(ModelRegistry)
            .filter(
                ModelRegistry.model_name == model.model_name,
                ModelRegistry.lifecycle_status == "ACTIVE",
                ModelRegistry.model_registry_id
                != model.model_registry_id,
            )
            .all()
        )

        for active_model in active_models:
            active_model.lifecycle_status = "INACTIVE"
            active_model.updated_at = datetime.utcnow()

        model.lifecycle_status = "ACTIVE"
        model.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(model)

        return model

    def deactivate_model(
        self,
        db: Session,
        model: ModelRegistry,
    ) -> ModelRegistry:

        if model.lifecycle_status != "ACTIVE":
            raise ValueError(
                "MODEL_NOT_ACTIVE"
            )

        model.lifecycle_status = "INACTIVE"
        model.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(model)

        return model

    def rollback_model(
        self,
        db: Session,
        current_model: ModelRegistry,
        rollback_model: ModelRegistry,
    ) -> ModelRegistry:

        if current_model.lifecycle_status != "ACTIVE":
            raise ValueError(
                "CURRENT_MODEL_NOT_ACTIVE"
            )

        if rollback_model.model_name != current_model.model_name:
            raise ValueError(
                "ROLLBACK_MODEL_NAME_MISMATCH"
            )

        if rollback_model.validation_status != "PASSED":
            raise ValueError(
                "ROLLBACK_MODEL_NOT_VALIDATED"
            )

        if rollback_model.lifecycle_status not in {
            "APPROVED",
            "INACTIVE",
            "ROLLED_BACK",
        }:
            raise ValueError(
                "ROLLBACK_MODEL_NOT_ELIGIBLE"
            )

        current_model.lifecycle_status = "ROLLED_BACK"
        current_model.updated_at = datetime.utcnow()

        rollback_model.lifecycle_status = "ACTIVE"
        rollback_model.rollback_of_version = (
            current_model.model_version
        )
        rollback_model.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(rollback_model)

        return rollback_model

    def list_versions(
        self,
        db: Session,
        model_name: str,
    ) -> list[ModelRegistry]:

        return (
            db.query(ModelRegistry)
            .filter(
                ModelRegistry.model_name == model_name
            )
            .order_by(
                ModelRegistry.created_at.desc()
            )
            .all()
        )

model_registry_service = ModelRegistryService()