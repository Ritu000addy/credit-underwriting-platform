import uuid

from sqlalchemy.orm import Session

from backend.app.models.document import Document
from backend.app.schemas.document import DocumentCreate


class DocumentService:

    def create_document(
        self,
        db: Session,
        document: DocumentCreate,
    ):
        record = Document(
            document_id=f"DOC-{uuid.uuid4().hex[:12].upper()}",
            application_id=document.application_id,
            document_type=document.document_type,
            document_name=document.document_name,
            document_category=document.document_category,
            document_reference=document.document_reference,
            document_source=document.document_source,
            verification_status=document.verification_status,
            verification_reference=document.verification_reference,
            extracted_data=document.extracted_data,
            analysis_reference=document.analysis_reference,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record


document_service = DocumentService()