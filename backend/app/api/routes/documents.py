from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
)
from backend.app.schemas.common import ApiResponse

from backend.app.services.document_service import document_service


router = APIRouter(
    prefix="/documents",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[DocumentResponse],
)
def create_document(
    document: DocumentCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    application_id = document.application_id

    log_workflow_event(
        workflow="document_creation",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="document_ingestion",
        entity_id=application_id,
    )

    try:
        result = document_service.create_document(
            db=db,
            document=document,
        )

    except Exception:
        log_workflow_event(
            workflow="document_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="document_ingestion",
            entity_id=application_id,
            error_code="DOCUMENT_CREATION_FAILED",
        )
        raise

    try:
        response_data = DocumentResponse.model_validate(result)
    except Exception:
        log_workflow_event(
            workflow="document_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="document_ingestion",
            entity_id=application_id,
            error_code="DOCUMENT_RESPONSE_VALIDATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="document_creation",
        event="completed",
        request=request,
        application_id=result.application_id,
        entity_type="document_ingestion",
        entity_id=application_id,
    )
    
    return success_response(
        request=request,
        data=response_data,
        message="Document data created successfully.",
    )