from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.workflow_logging import log_workflow_event
from backend.app.core.responses import success_response

from backend.app.schemas.device_behaviour import (
    DeviceBehaviourCreate,
    DeviceBehaviourResponse,
)
from backend.app.schemas.common import ApiResponse

from backend.app.services.device_behaviour_service import (
    device_behaviour_service,
)


router = APIRouter(
    prefix="/device-behaviour",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[DeviceBehaviourResponse],
)
def create_device_behaviour(
    device_behaviour: DeviceBehaviourCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    application_id = device_behaviour.application_id

    log_workflow_event(
        workflow="device_behaviour_creation",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="device_behaviour_analysis",
        entity_id=application_id,
    )

    try:
        result = device_behaviour_service.create_device_behaviour(
            db=db,
            device_behaviour=device_behaviour,
        )

    except Exception:
        log_workflow_event(
            workflow="device_behaviour_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="device_behaviour_analysis",
            entity_id=application_id,
            error_code="DEVICE_BEHAVIOUR_CREATION_FAILED",
        )
        raise

    try:
        response_data = DeviceBehaviourResponse.model_validate(result)

    except Exception:
        log_workflow_event(
            workflow="device_behaviour_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="device_behaviour_analysis",
            entity_id=application_id,
            error_code="DEVICE_BEHAVIOUR_RESPONSE_VALIDATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="device_behaviour_creation",
        event="completed",
        request=request,
        application_id=result.application_id,
        entity_type="device_behaviour_analysis",
        entity_id=application_id,
    )

    return success_response(
        request=request,
        data=response_data,
        message="Device / behaviour data created successfully.",
    )