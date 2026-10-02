from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.agreement import AgreementCreate, AgreementResponse, AgreementSign
from backend.app.services.agreement_service import agreement_service

router = APIRouter(
    prefix="/agreements",
    tags=["Agreement"],
)


@router.post(
    "",
    response_model=AgreementResponse,
)
def create_agreement(
    agreement: AgreementCreate,
    db: Session = Depends(get_db),
):
    agreement_id = f"AGR-{agreement.application_id}"

    result = agreement_service.create_agreement(
        db=db,
        agreement_id=agreement_id,
        application_id=agreement.application_id,
        sanction_id=agreement.sanction_id,
        agreement_status="CREATED",
        esign_status="NOT_STARTED",
        agreement_reference=agreement.agreement_reference,
        document_reference=agreement.document_reference,
        esign_provider=agreement.esign_provider,
        initiated_at=None,
        signed_at=None,
    )

    return result

@router.post(
    "/{agreement_id}/sign",
    response_model=AgreementResponse,
)
def update_agreement_sign(
    agreement_id: str,
    sign_request: AgreementSign,
    db: Session = Depends(get_db),
):
    agreement = db.get(
        __import__(
            "backend.app.models.agreement",
            fromlist=["Agreement"],
        ).Agreement,
        agreement_id,
    )

    if agreement is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Agreement not found",
        )

    if sign_request.esign_status == "INITIATED":
        if not sign_request.esign_reference:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400,
                detail="esign_reference is required when initiating eSign",
            )

        return agreement_service.initiate_esign(
            db=db,
            agreement=agreement,
            esign_provider=agreement.esign_provider or "UNKNOWN",
            esign_reference=sign_request.esign_reference,
        )

    return agreement_service.complete_esign(
        db=db,
        agreement=agreement,
        esign_status=sign_request.esign_status,
        esign_reference=sign_request.esign_reference,
        signed_at=sign_request.signed_at,
        failure_reason=sign_request.failure_reason,
    )