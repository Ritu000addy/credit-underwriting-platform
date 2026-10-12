import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.database import get_db

from backend.app.schemas.common import ApiResponse
from backend.app.schemas.model_registry import (
    ModelApprovalRequest,
    ModelRegistryCreate,
    ModelRegistryResponse,
    ModelRollbackRequest,
    ModelValidationComplete,
    ModelValidationStart,
    ModelVersionRequest,
)

from backend.app.services.audit_log_service import audit_log_service
from backend.app.services.model_registry_service import (
    model_registry_service,
)


router = APIRouter(
    prefix="/model-registry",
    tags=["Model Governance"],
)


@router.post(
    "",
    response_model=ApiResponse[ModelRegistryResponse],
)
def register_model(
    request: ModelRegistryCreate,
    api_request: Request,
    db: Session = Depends(get_db),
):
    log_workflow_event(
        workflow="model_registration",
        event="started",
        request=api_request,
        entity_type="model_registry",
        entity_id=request.model_registry_id,
    )

    try:
        result = model_registry_service.register_model(
            db=db,
            model_registry_id=request.model_registry_id,
            model_name=request.model_name,
            model_version=request.model_version,
            deployment_status=request.deployment_status,
            model_type=request.model_type,
            training_data_version=request.training_data_version,
            training_date=request.training_date,
            roc_auc=request.roc_auc,
            model_metrics=request.model_metrics,
            environment=request.environment,
            model_reference=request.model_reference,
            governance_notes=request.governance_notes,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference="MODEL_GOVERNANCE",
            action="MODEL_REGISTERED",
            entity_type="MODEL_REGISTRY",
            entity_reference=result.model_registry_id,
            description=(
                f"Model {result.model_name} "
                f"version {result.model_version} registered."
            ),
            previous_state=None,
            new_state=result.lifecycle_status,
            request_reference=result.model_registry_id,
            model_version=result.model_version,
        )

        db.commit()
        db.refresh(result)

        response_data = ModelRegistryResponse.model_validate(result)

    except ValueError as exc:
        log_workflow_event(
            workflow="model_registration",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=request.model_registry_id,
            error_code="MODEL_REGISTRATION_REJECTED",
        )
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="model_registration",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=request.model_registry_id,
            error_code="MODEL_REGISTRATION_FAILED",
        )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MODEL_REGISTRATION_FAILED",
        )

    log_workflow_event(
        workflow="model_registration",
        event="completed",
        request=api_request,
        entity_type="model_registry",
        entity_id=result.model_registry_id,
        status=result.lifecycle_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="Model registered successfully.",
        )


@router.post(
    "/validation/start",
    response_model=ApiResponse[ModelRegistryResponse],
)
def start_model_validation(
    request: ModelValidationStart,
    api_request: Request,
    db: Session = Depends(get_db),
):
    log_entity_id = f"{request.model_name}:{request.model_version}"

    log_workflow_event(
        workflow="model_validation_start",
        event="started",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
    )

    try:
        model = model_registry_service.get_model(
            db=db,
            model_name=request.model_name,
            model_version=request.model_version,
        )

    except Exception:
        log_workflow_event(
            workflow="model_validation_start",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_VALIDATION_START_FAILED",
        )
        raise

    if model is None:
        log_workflow_event(
            workflow="model_validation_start",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_NOT_FOUND",
        )
        raise HTTPException(
            status_code=404,
            detail="MODEL_NOT_FOUND",
        )

    try:
        result = model_registry_service.start_validation(
            db=db,
            model=model,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference="MODEL_VALIDATION",
            action="MODEL_VALIDATION_STARTED",
            entity_type="MODEL_REGISTRY",
            entity_reference=result.model_registry_id,
            description="Model validation started.",
            previous_state="REGISTERED",
            new_state=result.lifecycle_status,
            request_reference=result.model_registry_id,
            model_version=result.model_version,
        )

        db.commit()
        db.refresh(result)

        response_data = ModelRegistryResponse.model_validate(result)

    except ValueError as exc:
        log_workflow_event(
            workflow="model_validation_start",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_VALIDATION_START_REJECTED",
        )
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="model_validation_start",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_VALIDATION_START_FAILED",
        )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MODEL_VALIDATION_START_FAILED",
        )

    log_workflow_event(
        workflow="model_validation_start",
        event="completed",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
        status=result.lifecycle_status,
        )

    return success_response(
        request=api_request,
        data=response_data,
        message="Model validation started successfully.",
    )


@router.post(
    "/validation/complete",
    response_model=ApiResponse[ModelRegistryResponse],
)
def complete_model_validation(
    request: ModelValidationComplete,
    api_request: Request,
    db: Session = Depends(get_db),
):
    log_entity_id = f"{request.model_name}:{request.model_version}"

    log_workflow_event(
        workflow="model_validation_completion",
        event="started",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
    )

    try:
        model = model_registry_service.get_model(
            db=db,
            model_name=request.model_name,
            model_version=request.model_version,
        )

    except Exception:
        log_workflow_event(
            workflow="model_validation_completion",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_VALIDATION_COMPLETION_FAILED",
        )
        raise

    if model is None:
        log_workflow_event(
            workflow="model_validation_completion",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_NOT_FOUND",
        )
        raise HTTPException(
            status_code=404,
            detail="MODEL_NOT_FOUND",
        )

    try:
        result = model_registry_service.complete_validation(
            db=db,
            model=model,
            passed=request.passed,
            validated_by=request.validated_by,
            validation_notes=request.validation_notes,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference=request.validated_by,
            action="MODEL_VALIDATION_COMPLETED",
            entity_type="MODEL_REGISTRY",
            entity_reference=result.model_registry_id,
            description=(
                f"Model validation completed with status "
                f"{result.validation_status}."
            ),
            previous_state="VALIDATION",
            new_state=result.lifecycle_status,
            request_reference=result.model_registry_id,
            model_version=result.model_version,
        )

        db.commit()
        db.refresh(result)

        response_data = ModelRegistryResponse.model_validate(result)

    except ValueError as exc:
        log_workflow_event(
            workflow="model_validation_completion",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_VALIDATION_COMPLETION_REJECTED",
        )
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="model_validation_completion",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_VALIDATION_COMPLETION_FAILED",
        )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MODEL_VALIDATION_COMPLETION_FAILED",
        )

    log_workflow_event(
        workflow="model_validation_completion",
        event="completed",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
        status=result.lifecycle_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="Model validation completed successfully.",
    )



@router.post(
    "/approve",
    response_model=ApiResponse[ModelRegistryResponse],
)
def approve_model(
    request: ModelApprovalRequest,
    api_request: Request,
    db: Session = Depends(get_db),
):
    log_entity_id = f"{request.model_name}:{request.model_version}"

    log_workflow_event(
        workflow="model_approval",
        event="started",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
    )

    try:
        model = model_registry_service.get_model(
            db=db,
            model_name=request.model_name,
            model_version=request.model_version,
        )
    except Exception:
        log_workflow_event(
            workflow="model_approval",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_APPROVAL_FAILED",
        )
        raise

    if model is None:
        log_workflow_event(
            workflow="model_approval",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_NOT_FOUND",
        )
        raise HTTPException(
            status_code=404,
            detail="MODEL_NOT_FOUND",
        )

    try:
        previous_state = model.lifecycle_status

        result = model_registry_service.approve_model(
            db=db,
            model=model,
            approved_by=request.approved_by,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference=request.approved_by,
            action="MODEL_APPROVED",
            entity_type="MODEL_REGISTRY",
            entity_reference=result.model_registry_id,
            description=(
                f"Model version {result.model_version} approved."
            ),
            previous_state=previous_state,
            new_state=result.lifecycle_status,
            request_reference=result.model_registry_id,
            model_version=result.model_version,
        )

        db.commit()
        db.refresh(result)

        response_data = ModelRegistryResponse.model_validate(result)

    except ValueError as exc:
        log_workflow_event(
            workflow="model_approval",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_APPROVAL_REJECTED",
        )
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="model_approval",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_APPROVAL_FAILED",
        )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MODEL_APPROVAL_FAILED",
        )

    log_workflow_event(
        workflow="model_approval",
        event="completed",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
        status=result.lifecycle_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="Model approved successfully.",
        )


@router.post(
    "/activate",
    response_model=ApiResponse[ModelRegistryResponse],
)
def activate_model(
    request: ModelVersionRequest,
    api_request: Request,
    db: Session = Depends(get_db),
):

    log_entity_id = f"{request.model_name}:{request.model_version}"

    log_workflow_event(
        workflow="model_activation",
        event="started",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
    )

    try:
        model = model_registry_service.get_model(
            db=db,
            model_name=request.model_name,
            model_version=request.model_version,
        )
    except Exception:
        log_workflow_event(
            workflow="model_activation",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_ACTIVATION_FAILED",
        )
        raise

    if model is None:
        log_workflow_event(
            workflow="model_activation",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_NOT_FOUND",
        )
        raise HTTPException(
            status_code=404,
            detail="MODEL_NOT_FOUND",
        )

    try:
        previous_state = model.lifecycle_status

        result = model_registry_service.activate_model(
            db=db,
            model=model,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="SYSTEM",
            actor_reference="MODEL_GOVERNANCE",
            action="MODEL_ACTIVATED",
            entity_type="MODEL_REGISTRY",
            entity_reference=result.model_registry_id,
            description=(
                f"Model version {result.model_version} activated."
            ),
            previous_state=previous_state,
            new_state=result.lifecycle_status,
            request_reference=result.model_registry_id,
            model_version=result.model_version,
        )

        db.commit()
        db.refresh(result)

        response_data = ModelRegistryResponse.model_validate(result)

    except ValueError as exc:
        log_workflow_event(
            workflow="model_activation",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_ACTIVATION_REJECTED",
        )
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="model_activation",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_ACTIVATION_FAILED",
        )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MODEL_ACTIVATION_FAILED",
        )

    log_workflow_event(
        workflow="model_activation",
        event="completed",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
        status=result.lifecycle_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="Model activated successfully.",
    )



@router.post(
    "/deactivate",
    response_model=ApiResponse[ModelRegistryResponse],
)
def deactivate_model(
    request: ModelVersionRequest,
    api_request: Request,
    db: Session = Depends(get_db),
):
    log_entity_id = f"{request.model_name}:{request.model_version}"

    log_workflow_event(
        workflow="model_deactivation",
        event="started",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
    )

    try:
        model = model_registry_service.get_model(
            db=db,
            model_name=request.model_name,
            model_version=request.model_version,
        )
    except Exception:
        log_workflow_event(
            workflow="model_deactivation",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_DEACTIVATION_FAILED",
        )
        raise

    if model is None:
        log_workflow_event(
            workflow="model_deactivation",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_NOT_FOUND",
        )
        raise HTTPException(
            status_code=404,
            detail="MODEL_NOT_FOUND",
        )

    try:
        previous_state = model.lifecycle_status

        result = model_registry_service.deactivate_model(
            db=db,
            model=model,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference="MODEL_GOVERNANCE",
            action="MODEL_DEACTIVATED",
            entity_type="MODEL_REGISTRY",
            entity_reference=result.model_registry_id,
            description=(
                f"Model version {result.model_version} deactivated."
            ),
            previous_state=previous_state,
            new_state=result.lifecycle_status,
            request_reference=result.model_registry_id,
            model_version=result.model_version,
        )

        db.commit()
        db.refresh(result)

        response_data = ModelRegistryResponse.model_validate(result)

    except ValueError as exc:
        log_workflow_event(
            workflow="model_deactivation",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_DEACTIVATION_REJECTED",
        )
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="model_deactivation",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_DEACTIVATION_FAILED",
        )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MODEL_DEACTIVATION_FAILED",
        )

    log_workflow_event(
        workflow="model_deactivation",
        event="completed",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
        status=result.lifecycle_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="Model deactivated successfully.",
        )


@router.post(
    "/rollback",
    response_model=ApiResponse[ModelRegistryResponse],
)
def rollback_model(
    request: ModelRollbackRequest,
    api_request: Request,
    db: Session = Depends(get_db),
):
    log_entity_id = (
        f"{request.model_name}:"
        f"{request.current_version}->"
        f"{request.rollback_version}"
    )

    log_workflow_event(
        workflow="model_rollback",
        event="started",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
    )

    try:
        current_model = model_registry_service.get_model(
            db=db,
            model_name=request.model_name,
            model_version=request.current_version,
        )

        if current_model is None:
            log_workflow_event(
                workflow="model_rollback",
                event="failed",
                request=api_request,
                entity_type="model_registry",
                entity_id=log_entity_id,
                error_code="CURRENT_MODEL_NOT_FOUND",
            )
            raise HTTPException(
                status_code=404,
                detail="CURRENT_MODEL_NOT_FOUND",
            )

        rollback_model = model_registry_service.get_model(
            db=db,
            model_name=request.model_name,
            model_version=request.rollback_version,
        )

        if rollback_model is None:
            log_workflow_event(
                workflow="model_rollback",
                event="failed",
                request=api_request,
                entity_type="model_registry",
                entity_id=log_entity_id,
                error_code="ROLLBACK_MODEL_NOT_FOUND",
            )
            raise HTTPException(
                status_code=404,
                detail="ROLLBACK_MODEL_NOT_FOUND",
            )

        result = model_registry_service.rollback_model(
            db=db,
            current_model=current_model,
            rollback_model=rollback_model,
        )

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=None,
            actor_type="USER",
            actor_reference="MODEL_GOVERNANCE",
            action="MODEL_ROLLBACK",
            entity_type="MODEL_REGISTRY",
            entity_reference=result.model_registry_id,
            description=(
                f"Model rollback completed. "
                f"Active rollback target: {result.model_version}."
            ),
            previous_state="ACTIVE",
            new_state=result.lifecycle_status,
            request_reference=result.model_registry_id,
            model_version=result.model_version,
        )

        db.commit()
        db.refresh(result)

        response_data = ModelRegistryResponse.model_validate(result)

    except HTTPException:
        raise

    except ValueError as exc:
        log_workflow_event(
            workflow="model_rollback",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_ROLLBACK_REJECTED",
        )
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="model_rollback",
            event="failed",
            request=api_request,
            entity_type="model_registry",
            entity_id=log_entity_id,
            error_code="MODEL_ROLLBACK_FAILED",
        )
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="MODEL_ROLLBACK_FAILED",
        )

    log_workflow_event(
        workflow="model_rollback",
        event="completed",
        request=api_request,
        entity_type="model_registry",
        entity_id=log_entity_id,
        status=result.lifecycle_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="Model rollback completed successfully.",
    )


@router.get(
    "/{model_name}/versions",
    response_model=ApiResponse[list[ModelRegistryResponse]],
)
def list_model_versions(
    model_name: str,
    api_request: Request,
    db: Session = Depends(get_db),
):
    result = model_registry_service.list_versions(
        db=db,
        model_name=model_name,
    )

    response_data = [
        ModelRegistryResponse.model_validate(item)
        for item in result
    ]

    return success_response(
        request=api_request,
        data=response_data,
        message="Model versions retrieved successfully.",
    )


@router.get(
    "/{model_name}/active",
    response_model=ApiResponse[ModelRegistryResponse],
)
def get_active_model(
    model_name: str,
    api_request: Request,
    environment: str | None = None,
    db: Session = Depends(get_db),
):
    result = model_registry_service.get_active_model(
        db=db,
        model_name=model_name,
        environment=environment,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="ACTIVE_MODEL_NOT_FOUND",
        )

    response_data = ModelRegistryResponse.model_validate(result)

    return success_response(
        request=api_request,
        data=response_data,
        message="Active model retrieved successfully.",
    )


@router.get(
    "/{model_name}/{model_version}",
    response_model=ApiResponse[ModelRegistryResponse],
)
def get_model(
    model_name: str,
    model_version: str,
    api_request: Request,
    db: Session = Depends(get_db),
):
    result = model_registry_service.get_model(
        db=db,
        model_name=model_name,
        model_version=model_version,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="MODEL_NOT_FOUND",
        )

    response_data = ModelRegistryResponse.model_validate(result)

    return success_response(
        request=api_request,
        data=response_data,
        message="Model retrieved successfully.",
    )