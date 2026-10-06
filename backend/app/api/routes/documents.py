from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
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
    result = document_service.create_document(
        db=db,
        document=document,
    )

    response_data = DocumentResponse.model_validate(result)

    return success_response(
        request=request,
        data=response_data,
        message="Document data created successfully.",
    )