from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.schemas.bank_analysis import (
    BankAnalysisCreate,
    BankAnalysisResponse,
)
from backend.app.schemas.common import ApiResponse

from backend.app.services.bank_analysis_service import bank_analysis_service


router = APIRouter(
    prefix="/bank-analysis",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[BankAnalysisResponse],
)
def create_bank_analysis(
    analysis: BankAnalysisCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    application_id = analysis.application_id

    log_workflow_event(
        workflow="bank_analysis_creation",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="bank_analysis",
        entity_id=application_id,
    )
    try:
        result = bank_analysis_service.create_analysis(
            db=db,
            analysis=analysis,
        )

    except ValueError as exc:
        log_workflow_event(
            workflow="bank_analysis_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="bank_analysis",
            entity_id=application_id,
            error_code="BANK_ANALYSIS_CREATION_REJECTED",
        )
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow="bank_analysis_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="bank_analysis",
            entity_id=application_id,
            error_code="BANK_ANALYSIS_CREATION_FAILED",
        )
        raise

    try:
        response_data = BankAnalysisResponse.model_validate(result)
    except Exception:
        log_workflow_event(
            workflow="bank_analysis_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="bank_analysis",
            entity_id=application_id,
            error_code="BANK_ANALYSIS_RESPONSE_VALIDATION_FAILED",
        )
        raise
    
    log_workflow_event(
        workflow="bank_analysis_creation",
        event="completed",
        request=request,
        application_id=result.application_id,
        entity_type="bank_analysis",
        entity_id=application_id,
    )

    return success_response(
        request=request,
        data=response_data,
        message="Bank analysis created successfully.",
    )