from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.schemas.employment import (
    EmploymentCreate,
    EmploymentResponse,
)
from backend.app.schemas.common import ApiResponse

from backend.app.services.employment_service import employment_service


router = APIRouter(
    prefix="/employment",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[EmploymentResponse],
)
def create_employment(
    employment: EmploymentCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    application_id = employment.application_id

    log_workflow_event(
        workflow="employment_creation",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="employment_analysis",
        entity_id=application_id,
    )

    try:
        result = employment_service.create_employment(
            db=db,
            employment=employment,
        )

    except Exception:
        log_workflow_event(
            workflow="employment_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="employment_analysis",
            entity_id=application_id,
            error_code="EMPLOYMENT_CREATION_FAILED",
        )
        raise

    try:
        response_data = EmploymentResponse.model_validate(result)
    except Exception:
        log_workflow_event(
            workflow="employment_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="employment_analysis",
            entity_id=application_id,
            error_code="EMPLOYMENT_RESPONSE_VALIDATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="employment_creation",
        event="completed",
        request=request,
        application_id=result.application_id,
        entity_type="employment_analysis",
        entity_id=application_id,
    )

    return success_response(
        request=request,
        data=response_data,
        message="Employment / business data created successfully.",
    )