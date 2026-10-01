from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.document import DocumentCreate
from backend.app.services.document_service import document_service


router = APIRouter(
    prefix="/documents",
    tags=["Source Data Ingestion"],
)


@router.post("")
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
):
    result = document_service.create_document(
        db=db,
        document=document,
    )

    return {
        "message": "Document data created successfully",
        "document": {
            "document_id": result.document_id,
            "application_id": result.application_id,
            "document_type": result.document_type,
            "document_name": result.document_name,
            "document_category": result.document_category,
            "document_reference": result.document_reference,
            "document_source": result.document_source,
            "verification_status": result.verification_status,
            "verification_reference": result.verification_reference,
            "extracted_data": result.extracted_data,
            "analysis_reference": result.analysis_reference,
            "created_at": result.created_at,
        },
    }