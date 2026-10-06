from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.mandate import Mandate
from backend.app.schemas.mandate import (
    MandateCreate,
    MandateResponse,
    MandateUpdate,
)
from backend.app.schemas.common import ApiResponse
from backend.app.core.responses import success_response
from backend.app.services.mandate_service import mandate_service


router = APIRouter(
    prefix="/mandates",
    tags=["Mandate"],
)


@router.post(
    "",
    response_model=ApiResponse[MandateResponse],
)
def create_mandate(
    mandate: MandateCreate,
    request: Request,
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

        response_data = MandateResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Mandate created successfully.",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/{mandate_id}/status",
    response_model=ApiResponse[MandateResponse],
)
def update_mandate_status(
    mandate_id: str,
    update: MandateUpdate,
    request: Request,
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
            result = mandate_service.initiate_mandate(
                db=db,
                mandate=mandate,
            )

            response_data = MandateResponse.model_validate(result)

            return success_response(
                request=request,
                data=response_data,
                message="Mandate initiated successfully.",
            )

        result = mandate_service.complete_mandate(
            db=db,
            mandate=mandate,
            status=update.status,
            failure_reason=update.failure_reason,
            completed_at=update.completed_at,
        )

        response_data = MandateResponse.model_validate(result)

        return success_response(
            request=request,
            data=response_data,
            message="Mandate status updated successfully.",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )