from datetime import datetime

from pydantic import BaseModel


class AgreementCreate(BaseModel):
    application_id: str
    sanction_id: str

    agreement_reference: str | None = None
    document_reference: str | None = None

    esign_provider: str | None = None


class AgreementSign(BaseModel):
    esign_status: str
    esign_reference: str | None = None
    failure_reason: str | None = None
    signed_at: datetime | None = None


class AgreementResponse(BaseModel):
    agreement_id: str
    application_id: str
    sanction_id: str

    agreement_reference: str | None = None
    agreement_status: str

    esign_status: str
    esign_provider: str | None = None
    esign_reference: str | None = None

    document_reference: str | None = None
    failure_reason: str | None = None

    initiated_at: datetime | None = None
    signed_at: datetime | None = None