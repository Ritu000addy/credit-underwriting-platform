import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.sanction import Sanction
from backend.app.schemas.sanction import (
    SanctionCreate,
    SanctionResponse,
)
from backend.app.services.sanction_service import sanction_service


router = APIRouter(
    prefix="/sanctions",
    tags=["Sanctions"],
)


@router.post(
    "",
    response_model=SanctionResponse,
)
def create_sanction(
    sanction: SanctionCreate,
    db: Session = Depends(get_db),
):
    sanction_id = f"SAN-{uuid.uuid4().hex[:12].upper()}"

    try:
        result = sanction_service.create_sanction(
            db=db,
            sanction_id=sanction_id,
            application_id=sanction.application_id,
            sanctioned_amount=sanction.sanctioned_amount,
            sanctioned_tenure=sanction.sanctioned_tenure,
            sanctioned_emi=sanction.sanctioned_emi,
            interest_rate=sanction.interest_rate,
            sanction_status="APPROVED",
            approval_authority=sanction.approval_authority,
            terms_and_conditions=sanction.terms_and_conditions,
            expires_at=sanction.expires_at,
        )

        return result

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/{sanction_id}",
    response_model=SanctionResponse,
)
def get_sanction(
    sanction_id: str,
    db: Session = Depends(get_db),
):
    result = db.get(
        Sanction,
        sanction_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Sanction not found",
        )

    return result