from pydantic import BaseModel
from typing import Optional


class DocumentCreate(BaseModel):
    application_id: str

    document_type: str
    document_name: Optional[str] = None
    document_category: Optional[str] = None

    document_reference: Optional[str] = None
    document_source: Optional[str] = None

    verification_status: Optional[str] = None
    verification_reference: Optional[str] = None

    extracted_data: Optional[str] = None
    analysis_reference: Optional[str] = None