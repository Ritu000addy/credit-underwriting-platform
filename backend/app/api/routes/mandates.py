from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.models.mandate import Mandate

from backend.app.schemas.mandate import (
    MandateCreate,
    MandateResponse,
    MandateUpdate,
)
from backend.app.schemas.common import ApiResponse

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

    log_workflow_event(
        workflow="mandate_creation",
        event="started",
        request=request,
        application_id=mandate.application_id,
        entity_type="mandate",
        entity_id=mandate_id,
    )

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

    except ValueError as exc:
        db.rollback()
        log_workflow_event(
            workflow="mandate_creation",
            event="failed",
            request=request,
            application_id=mandate.application_id,
            entity_type="mandate",
            entity_id=mandate_id,
            error_code="MANDATE_CREATION_FAILED",
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        log_workflow_event(
            workflow="mandate_creation",
            event="failed",
            request=request,
            application_id=mandate.application_id,
            entity_type="mandate",
            entity_id=mandate_id,
            error_code="MANDATE_CREATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="mandate_creation",
        event="completed",
        request=request,
        application_id=mandate.application_id,
        entity_type="mandate",
        entity_id=mandate_id,
        status="CREATED",
    )

    return success_response(
        request=request,
        data=response_data,
        message="Mandate created successfully.",
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

    workflow_name = (
        "mandate_initiation"
        if update.status == "INITIATED"
        else "mandate_completion"
    )

    mandate = db.get(Mandate, mandate_id)

    if mandate is None:
        log_workflow_event(
            workflow=workflow_name,
            event="failed",
            request=request,
            entity_type="mandate",
            entity_id=mandate_id,
            status=update.status,
            error_code="MANDATE_NOT_FOUND",
        )

        raise HTTPException(
            status_code=404,
            detail="Mandate not found",
        )

    log_workflow_event(
        workflow=workflow_name,
        event="started",
        request=request,
        application_id=mandate.application_id,
        entity_type="mandate",
        entity_id=mandate_id,
        status=update.status,
    )

    try:
        if update.status == "INITIATED":
            result = mandate_service.initiate_mandate(
                db=db,
                mandate=mandate,
            )

            response_message = "Mandate initiated successfully."

        else:
            result = mandate_service.complete_mandate(
                db=db,
                mandate=mandate,
                status=update.status,
                failure_reason=update.failure_reason,
                completed_at=update.completed_at,
            )
            response_message = "Mandate status updated successfully."

        response_data = MandateResponse.model_validate(result)

    except ValueError as exc:
        db.rollback()
        log_workflow_event(
            workflow=workflow_name,
            event="failed",
            request=request,
            application_id=mandate.application_id,
            entity_type="mandate",
            entity_id=mandate_id,
            status=update.status,
            error_code="MANDATE_STATUS_UPDATE_FAILED",
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        log_workflow_event(
            workflow=workflow_name,
            event="failed",
            request=request,
            application_id=mandate.application_id,
            entity_type="mandate",
            entity_id=mandate_id,
            status=update.status,
            error_code="MANDATE_STATUS_UPDATE_FAILED",
        )
        raise

    log_workflow_event(
        workflow=workflow_name,
        event="completed",
        request=request,
        application_id=mandate.application_id,
        entity_type="mandate",
        entity_id=mandate_id,
        status=update.status,
    )

    return success_response(
        request=request,
        data=response_data,
        message=response_message,
    )