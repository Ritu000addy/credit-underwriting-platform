from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict


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


class DocumentResponse(DocumentCreate):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    created_at: datetime