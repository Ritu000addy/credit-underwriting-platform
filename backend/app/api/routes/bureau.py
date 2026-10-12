from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.schemas.bureau import (
    BureauReportCreate,
    BureauReportResponse,
)
from backend.app.schemas.common import ApiResponse

from backend.app.services.bureau_report_service import bureau_report_service


router = APIRouter(
    prefix="/bureau-reports",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[BureauReportResponse],
)
def create_bureau_report(
    report: BureauReportCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    application_id = report.application_id

    log_workflow_event(
        workflow="bureau_report_creation",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="bureau_report",
        entity_id=application_id,
    )

    try:
        result = bureau_report_service.create_report(
            db=db,
            report=report,
        )

    except ValueError as exc:
        log_workflow_event(
            workflow="bureau_report_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="bureau_report",
            entity_id=application_id,
            error_code="BUREAU_REPORT_CREATION_REJECTED",
        )
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="bureau_report_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="bureau_report",
            entity_id=application_id,
            error_code="BUREAU_REPORT_CREATION_FAILED",
        )
        raise

    try:
        response_data = BureauReportResponse.model_validate(result)
    except Exception:
        log_workflow_event(
            workflow="bureau_report_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="bureau_report",
            entity_id=application_id,
            error_code="BUREAU_REPORT_RESPONSE_VALIDATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="bureau_report_creation",
        event="completed",
        request=request,
        application_id=result.application_id,
        entity_type="bureau_report",
        entity_id=application_id,
    )

    return success_response(
        request=request,
        data=response_data,
        message="Bureau report created successfully.",
    )