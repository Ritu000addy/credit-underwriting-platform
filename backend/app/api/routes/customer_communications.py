from fastapi import APIRouter, HTTPException, Request, Depends

from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.models.loan_application import LoanApplication
from backend.app.models.sanction import Sanction
from backend.app.models.disbursement import Disbursement
from backend.app.models.repayment import Repayment
from backend.app.models.repayment_schedule import RepaymentSchedule

from backend.app.schemas.common import ApiResponse
from backend.app.schemas.customer_communication import (
    AdditionalInformationRequestInput,
    CustomerCommunicationDraft,
    DecisionCommunicationInput,
    SanctionCommunicationInput,
    DisbursementCommunicationInput,
    RepaymentServicingCommunicationInput,
)

from backend.app.services.customer_communication_service import (
    customer_communication_service,
)


router = APIRouter(
    prefix="/customer-communications",
    tags=["Customer Communications"],
)

def _validate_application_customer(
    db: Session,
    application_id: str,
    customer_id: str,
) -> None:
    application = db.get(LoanApplication, application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="APPLICATION_NOT_FOUND",
        )

    if application.customer_id != customer_id:
        raise HTTPException(
            status_code=409,
            detail="APPLICATION_CUSTOMER_MISMATCH",
        )


def _log_source_communication_event(
    *,
    request: Request,
    workflow: str,
    event: str,
    application_id: str,
    status: str | None = None,
    error_code: str | None = None,
) -> None:
    log_workflow_event(
        workflow=workflow,
        event=event,
        request=request,
        application_id=application_id,
        entity_type="customer_communication_draft",
        entity_id=application_id,
        status=status,
        error_code=error_code,
    )


@router.post(
    "/additional-information-request",
    response_model=ApiResponse[CustomerCommunicationDraft],
)
def create_additional_information_request(
    payload: AdditionalInformationRequestInput,
    request: Request,
) -> ApiResponse[CustomerCommunicationDraft]:

    application_id = payload.application_id

    log_workflow_event(
        workflow="additional_information_request_draft",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="customer_communication_draft",
        entity_id=application_id,
    )

    try:
        draft = (
            customer_communication_service
            .generate_additional_information_request(payload)
        )

    except ValueError as exc:
        log_workflow_event(
            workflow="additional_information_request_draft",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="customer_communication_draft",
            entity_id=application_id,
            error_code="ADDITIONAL_INFORMATION_DRAFT_REJECTED",
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception:
        log_workflow_event(
            workflow="additional_information_request_draft",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="customer_communication_draft",
            entity_id=application_id,
            error_code="ADDITIONAL_INFORMATION_DRAFT_FAILED",
        )
        raise

    log_workflow_event(
        workflow="additional_information_request_draft",
        event="completed",
        request=request,
        application_id=application_id,
        entity_type="customer_communication_draft",
        entity_id=application_id,
        status=draft.status,
    )

    return success_response(
        data=draft,
        message="Additional-information request draft generated successfully.",
        request=request,
    )


@router.post(
    "/decision-draft",
    response_model=ApiResponse[CustomerCommunicationDraft],
)
def create_decision_communication_draft(
    payload: DecisionCommunicationInput,
    request: Request,
) -> ApiResponse[CustomerCommunicationDraft]:
    application_id = payload.underwriting.application_id

    log_workflow_event(
        workflow="decision_communication_draft",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="customer_communication_draft",
        entity_id=application_id,
    )

    try:
        draft = (
            customer_communication_service
            .generate_decision_communication(payload)
        )

    except ValueError as exc:
        log_workflow_event(
            workflow="decision_communication_draft",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="customer_communication_draft",
            entity_id=application_id,
            error_code="DECISION_COMMUNICATION_DRAFT_REJECTED",
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception:
        log_workflow_event(
            workflow="decision_communication_draft",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="customer_communication_draft",
            entity_id=application_id,
            error_code="DECISION_COMMUNICATION_DRAFT_FAILED",
        )
        raise

    log_workflow_event(
        workflow="decision_communication_draft",
        event="completed",
        request=request,
        application_id=application_id,
        entity_type="customer_communication_draft",
        entity_id=application_id,
        status=draft.status,
    )

    return success_response(
        data=draft,
        message="Decision communication draft generated successfully.",
        request=request,
    )


# Sanction communication
@router.post(
    "/sanction-draft",
    response_model=ApiResponse[CustomerCommunicationDraft],
)
def create_sanction_communication_draft(
    payload: SanctionCommunicationInput,
    request: Request,
    db: Session = Depends(get_db),
):
    workflow = "sanction_communication_draft"
    app_id = payload.application_id

    _log_source_communication_event(
        request=request,
        workflow=workflow,
        event="started",
        application_id=app_id,
    )

    try:
        _validate_application_customer(db, app_id, payload.customer_id)

        sanction = (
            db.query(Sanction)
            .filter(Sanction.application_id == app_id)
            .order_by(Sanction.created_at.desc())
            .first()
        )

        draft = customer_communication_service.generate_sanction_communication(
            payload,
            sanction,
        )

    except HTTPException:
        _log_source_communication_event(
            request=request,
            workflow=workflow,
            event="failed",
            application_id=app_id,
            error_code="COMMUNICATION_SOURCE_VALIDATION_FAILED",
        )
        raise

    except ValueError as exc:
        _log_source_communication_event(
            request=request,
            workflow=workflow,
            event="failed",
            application_id=app_id,
            error_code="SANCTION_COMMUNICATION_DRAFT_REJECTED",
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception:
        _log_source_communication_event(
            request=request,
            workflow=workflow,
            event="failed",
            application_id=app_id,
            error_code="SANCTION_COMMUNICATION_DRAFT_FAILED",
        )
        raise

    _log_source_communication_event(
        request=request,
        workflow=workflow,
        event="completed",
        application_id=app_id,
        status=draft.status,
    )

    return success_response(
        request=request,
        data=draft,
        message="Sanction communication draft generated successfully.",
    )

# Disbursement communication
@router.post(
    "/disbursement-draft",
    response_model=ApiResponse[CustomerCommunicationDraft],
)
def create_disbursement_communication_draft(
    payload: DisbursementCommunicationInput,
    request: Request,
    db: Session = Depends(get_db),
):
    workflow = "disbursement_communication_draft"
    app_id = payload.application_id

    _log_source_communication_event(
        request=request,
        workflow=workflow,
        event="started",
        application_id=app_id,
    )

    try:
        _validate_application_customer(db, app_id, payload.customer_id)

        disbursement = (
            db.query(Disbursement)
            .filter(Disbursement.application_id == app_id)
            .order_by(Disbursement.created_at.desc())
            .first()
        )

        draft = (
            customer_communication_service
            .generate_disbursement_communication(
                payload,
                disbursement,
            )
        )

    except HTTPException:
        _log_source_communication_event(
            request=request,
            workflow=workflow,
            event="failed",
            application_id=app_id,
            error_code="COMMUNICATION_SOURCE_VALIDATION_FAILED",
        )
        raise

    except ValueError as exc:
        _log_source_communication_event(
            request=request,
            workflow=workflow,
            event="failed",
            application_id=app_id,
            error_code="DISBURSEMENT_COMMUNICATION_DRAFT_REJECTED",
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception:
        _log_source_communication_event(
            request=request,
            workflow=workflow,
            event="failed",
            application_id=app_id,
            error_code="DISBURSEMENT_COMMUNICATION_DRAFT_FAILED",
        )
        raise

    _log_source_communication_event(
        request=request,
        workflow=workflow,
        event="completed",
        application_id=app_id,
        status=draft.status,
    )

    return success_response(
        request=request,
        data=draft,
        message="Disbursement communication draft generated successfully.",
    )

# Repayment / servicing communication
@router.post(
    "/repayment-servicing-draft",
    response_model=ApiResponse[CustomerCommunicationDraft],
)
def create_repayment_servicing_communication_draft(
    payload: RepaymentServicingCommunicationInput,
    request: Request,
    db: Session = Depends(get_db),
):
    workflow = "repayment_servicing_communication_draft"
    app_id = payload.application_id

    _log_source_communication_event(
        request=request,
        workflow=workflow,
        event="started",
        application_id=app_id,
    )

    try:
        _validate_application_customer(db, app_id, payload.customer_id)

        schedule = db.get(
            RepaymentSchedule,
            payload.repayment_schedule_id,
        )

        repayment = None
        if schedule is not None and schedule.status == "PAID":
            repayment = (
                db.query(Repayment)
                .filter(
                    Repayment.repayment_schedule_id
                    == payload.repayment_schedule_id,
                    Repayment.status == "SUCCESS",
                )
                .order_by(Repayment.paid_at.desc())
                .first()
            )

        draft = (
            customer_communication_service
            .generate_repayment_servicing_communication(
                payload,
                schedule,
                repayment,
            )
        )

    except HTTPException:
        _log_source_communication_event(
            request=request,
            workflow=workflow,
            event="failed",
            application_id=app_id,
            error_code="COMMUNICATION_SOURCE_VALIDATION_FAILED",
        )
        raise

    except ValueError as exc:
        _log_source_communication_event(
            request=request,
            workflow=workflow,
            event="failed",
            application_id=app_id,
            error_code="REPAYMENT_SERVICING_DRAFT_REJECTED",
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception:
        _log_source_communication_event(
            request=request,
            workflow=workflow,
            event="failed",
            application_id=app_id,
            error_code="REPAYMENT_SERVICING_DRAFT_FAILED",
        )
        raise

    _log_source_communication_event(
        request=request,
        workflow=workflow,
        event="completed",
        application_id=app_id,
        status=draft.status,
    )

    return success_response(
        request=request,
        data=draft,
        message="Repayment/servicing communication draft generated successfully.",
    )