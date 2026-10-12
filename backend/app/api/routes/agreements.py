from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.models.agreement import Agreement

from backend.app.schemas.agreement import (
    AgreementCreate,
    AgreementResponse,
    AgreementSign,
)
from backend.app.schemas.common import ApiResponse

from backend.app.services.agreement_service import agreement_service


router = APIRouter(
    prefix="/agreements",
    tags=["Agreement"],
)


@router.post(
    "",
    response_model=ApiResponse[AgreementResponse],
)
def create_agreement(
    agreement: AgreementCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    agreement_id = f"AGR-{agreement.application_id}"

    log_workflow_event(
        workflow="agreement_creation",
        event="started",
        request=request,
        application_id=agreement.application_id,
        entity_type="agreement",
        entity_id=agreement_id,
    )

    try:
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

        response_data = AgreementResponse.model_validate(result)
    
    except Exception:
        log_workflow_event(
            workflow="agreement_creation",
            event="failed",
            request=request,
            application_id=agreement.application_id,
            entity_type="agreement",
            entity_id=agreement_id,
            error_code="AGREEMENT_CREATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="agreement_creation",
        event="completed",
        request=request,
        application_id=agreement.application_id,
        entity_type="agreement",
        entity_id=agreement_id,
        status="CREATED",
    )

    return success_response(
        request=request,
        data=response_data,
        message="Agreement created successfully.",
    )


@router.post(
    "/{agreement_id}/sign",
    response_model=ApiResponse[AgreementResponse],
)
def update_agreement_sign(
    agreement_id: str,
    sign_request: AgreementSign,
    request: Request,
    db: Session = Depends(get_db),
):
    agreement = db.get(
        Agreement,
        agreement_id,
    )

    if agreement is None:
        workflow = (
            "agreement_esign_initiation"
            if sign_request.esign_status == "INITIATED"
            else "agreement_esign_completion"
        )

        log_workflow_event(
            workflow=workflow,
            event="failed",
            request=request,
            entity_type="agreement",
            entity_id=agreement_id,
            error_code="AGREEMENT_NOT_FOUND",
        )

        raise HTTPException(
            status_code=404,
            detail="Agreement not found",
        )

    if sign_request.esign_status == "INITIATED":
        log_workflow_event(
            workflow="agreement_esign_initiation",
            event="started",
            request=request,
            application_id=agreement.application_id,
            entity_type="agreement",
            entity_id=agreement_id,
        )

        try:
            if not sign_request.esign_reference:
                raise HTTPException(
                    status_code=400,
                    detail="esign_reference is required when initiating eSign",
                )

            result = agreement_service.initiate_esign(
                db=db,
                agreement=agreement,
                esign_provider=agreement.esign_provider or "UNKNOWN",
                esign_reference=sign_request.esign_reference,
            )

            response_data = AgreementResponse.model_validate(result)
        
        except Exception:
            log_workflow_event(
                workflow="agreement_esign_initiation",
                event="failed",
                request=request,
                application_id=agreement.application_id,
                entity_type="agreement",
                entity_id=agreement_id,
                error_code="AGREEMENT_ESIGN_INITIATION_FAILED",
            )
            raise

        log_workflow_event(
            workflow="agreement_esign_initiation",
            event="completed",
            request=request,
            application_id=agreement.application_id,
            entity_type="agreement",
            entity_id=agreement_id,
            status="INITIATED",
        )

        return success_response(
            request=request,
            data=response_data,
            message="Agreement eSign initiated successfully.",
        )

    # E-sign completion or status update
    log_workflow_event(
        workflow="agreement_esign_completion",
        event="started",
        request=request,
        application_id=agreement.application_id,
        entity_type="agreement",
        entity_id=agreement_id,
    )

    try:
        result = agreement_service.complete_esign(
            db=db,
            agreement=agreement,
            esign_status=sign_request.esign_status,
            esign_reference=sign_request.esign_reference,
            signed_at=sign_request.signed_at,
            failure_reason=sign_request.failure_reason,
        )

        response_data = AgreementResponse.model_validate(result)
    
    except Exception:
        log_workflow_event(
            workflow="agreement_esign_completion",
            event="failed",
            request=request,
            application_id=agreement.application_id,
            entity_type="agreement",
            entity_id=agreement_id,
            error_code="AGREEMENT_ESIGN_COMPLETION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="agreement_esign_completion",
        event="completed",
        request=request,
        application_id=agreement.application_id,
        entity_type="agreement",
        entity_id=agreement_id,
        status=sign_request.esign_status,
    )

    return success_response(
        request=request,
        data=response_data,
        message="Agreement eSign status updated successfully.",
    )