from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.database import get_db

from backend.app.schemas.application import ApplicationCreate, ApplicationResponse
from backend.app.schemas.common import ApiResponse

from backend.app.services.application_service import application_service

router = APIRouter(
    prefix="/applications",
    tags=["LOS Origination"],
)

@router.post(
    "",
    response_model=ApiResponse[ApplicationResponse])

def create_application(
    application: ApplicationCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    application_id = application.application_id

    log_workflow_event(
        workflow="application_creation",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="loan_application",
        entity_id=application_id,
    )

    try:
        result = application_service.create_application(
            db=db,
            application=application,
        )

        response_data = ApplicationResponse.model_validate(
            result
        )

        response = success_response(
            request=request,
            data=response_data,
            message="Application created successfully.",
        )

    except ValueError as exc:
        log_workflow_event(
            workflow="application_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="loan_application",
            entity_id=application_id,
            error_code="APPLICATION_CREATION_REJECTED",
        )
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="application_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="loan_application",
            entity_id=application_id,
            error_code="APPLICATION_CREATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="application_creation",
        event="completed",
        request=request,
        application_id=result.application_id,
        entity_type="loan_application",
        entity_id=result.application_id,
        status=result.status,
    )

    return response


@router.get(
    "/{application_id}",
    response_model=ApiResponse[ApplicationResponse],
)
def get_application(
    application_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    result = application_service.get_application(
        db=db,
        application_id=application_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    response_data = ApplicationResponse.model_validate(
        result
    )

    return success_response(
        request=request,
        data=response_data,
        message="Application retrieved successfully.",
    )