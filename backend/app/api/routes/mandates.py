from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.mandate import Mandate
from backend.app.schemas.mandate import (
    MandateCreate,
    MandateResponse,
    MandateUpdate,
)
from backend.app.services.mandate_service import mandate_service

router = APIRouter(
    prefix="/mandates",
    tags=["Mandate"],
)


@router.post(
    "",
    response_model=MandateResponse,
)
def create_mandate(
    mandate: MandateCreate,
    db: Session = Depends(get_db),
):
    mandate_id = f"MANDATE-{mandate.application_id}"

    try:
        result = mandate_service.create_mandate(
            db=db,
            mandate_id=mandate_id,
            application_id=mandate.application_id,
            status="CREATED",
            mandate_reference=mandate.mandate_reference,
            mandate_type=mandate.mandate_type,
            provider=mandate.provider,
        )
        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.post(
    "/{mandate_id}/status",
    response_model=MandateResponse,
)
def update_mandate_status(
    mandate_id: str,
    update: MandateUpdate,
    db: Session = Depends(get_db),
):
    mandate = db.get(Mandate, mandate_id)

    if mandate is None:
        raise HTTPException(
            status_code=404,
            detail="Mandate not found",
        )

    try:
        if update.status == "INITIATED":
            return mandate_service.initiate_mandate(
                db=db,
                mandate=mandate,
            )

        return mandate_service.complete_mandate(
            db=db,
            mandate=mandate,
            status=update.status,
            failure_reason=update.failure_reason,
            completed_at=update.completed_at,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )