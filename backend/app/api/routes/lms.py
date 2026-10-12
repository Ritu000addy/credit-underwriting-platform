from fastapi import APIRouter, Request

from backend.app.core.responses import success_response
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.integrations.lms.schemas import (
    LMSSanctionRequest,
    LMSSanctionResponse,
    LMSRepaymentScheduleRequest,
    LMSRepaymentScheduleResponse,
    LMSServicingInstallmentRequest,
    LMSServicingInstallmentResponse,
    LMSLoanStatusRequest,
    LMSLoanStatusResponse,
)
from backend.app.integrations.lms.service import lms_service

from backend.app.schemas.common import ApiResponse


router = APIRouter(
    prefix="/lms",
    tags=["LMS Integration"],
)


@router.post(
    "/sanctions",
    response_model=ApiResponse[LMSSanctionResponse],
)
def create_lms_loan_account(
    request: LMSSanctionRequest,
    api_request: Request,
):
    log_workflow_event(
        workflow="lms_loan_account_creation",
        event="started",
        request=api_request,
        application_id=request.application_id,
        entity_type="lms_sanction",
        entity_id=request.sanction_id,
    )

    try:
        result = lms_service.create_loan_account(request)

        response_data = LMSSanctionResponse.model_validate(result)

    except Exception:
        log_workflow_event(
            workflow="lms_loan_account_creation",
            event="failed",
            request=api_request,
            application_id=request.application_id,
            entity_type="lms_sanction",
            entity_id=request.sanction_id,
            error_code="LMS_LOAN_ACCOUNT_CREATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="lms_loan_account_creation",
        event="completed",
        request=api_request,
        application_id=request.application_id,
        entity_type="lms_sanction",
        entity_id=request.sanction_id,
        status=response_data.loan_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="LMS loan account created successfully.",
    )


@router.post(
    "/loan-status",
    response_model=ApiResponse[LMSLoanStatusResponse],
)
def update_lms_loan_status(
    request: LMSLoanStatusRequest,
    api_request: Request,
):
    log_workflow_event(
        workflow="lms_loan_status_update",
        event="started",
        request=api_request,
        application_id=request.application_id,
        entity_type="lms_loan_account",
        entity_id=request.loan_account_id,
        status=request.loan_status,
    )

    try:
        result = lms_service.update_loan_status(request)

        response_data = LMSLoanStatusResponse.model_validate(result)

    except Exception:
        log_workflow_event(
            workflow="lms_loan_status_update",
            event="failed",
            request=api_request,
            application_id=request.application_id,
            entity_type="lms_loan_account",
            entity_id=request.loan_account_id,
            error_code="LMS_LOAN_STATUS_UPDATE_FAILED",
        )
        raise

    log_workflow_event(
        workflow="lms_loan_status_update",
        event="completed",
        request=api_request,
        application_id=request.application_id,
        entity_type="lms_loan_account",
        entity_id=request.loan_account_id,
        status=response_data.loan_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="LMS loan status updated successfully.",
    )


@router.post(
    "/repayment-schedules",
    response_model=ApiResponse[LMSRepaymentScheduleResponse],
)
def create_lms_repayment_schedule(
    request: LMSRepaymentScheduleRequest,
    api_request: Request,
):
    schedule_request_id = (
        f"{request.loan_account_id}:{request.sanction_id}"
    )

    log_workflow_event(
        workflow="lms_repayment_schedule_creation",
        event="started",
        request=api_request,
        application_id=request.application_id,
        entity_type="lms_repayment_schedule",
        entity_id=schedule_request_id,
    )

    try:    
        result = lms_service.create_repayment_schedule(request)

        response_data = LMSRepaymentScheduleResponse.model_validate(result)

    except Exception:
        log_workflow_event(
            workflow="lms_repayment_schedule_creation",
            event="failed",
            request=api_request,
            application_id=request.application_id,
            entity_type="lms_repayment_schedule",
            entity_id=schedule_request_id,
            error_code="LMS_REPAYMENT_SCHEDULE_CREATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="lms_repayment_schedule_creation",
        event="completed",
        request=api_request,
        application_id=request.application_id,
        entity_type="lms_repayment_schedule",
        entity_id=schedule_request_id,
        status=response_data.schedule_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="LMS repayment schedule created successfully.",
    )


@router.post(
    "/servicing/installments",
    response_model=ApiResponse[LMSServicingInstallmentResponse],
)
def create_lms_servicing_installment(
    request: LMSServicingInstallmentRequest,
    api_request: Request,
):
    installment_request_id = (
        f"{request.repayment_schedule_id}:{request.installment_number}"
    )

    log_workflow_event(
        workflow="lms_servicing_installment_creation",
        event="started",
        request=api_request,
        application_id=request.application_id,
        entity_type="lms_servicing_installment",
        entity_id=installment_request_id,
    )

    try:
        result = lms_service.create_servicing_installment(request)

        response_data = LMSServicingInstallmentResponse.model_validate(result)

    except Exception:
        log_workflow_event(
            workflow="lms_servicing_installment_creation",
            event="failed",
            request=api_request,
            application_id=request.application_id,
            entity_type="lms_servicing_installment",
            entity_id=installment_request_id,
            error_code="LMS_SERVICING_INSTALLMENT_CREATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="lms_servicing_installment_creation",
        event="completed",
        request=api_request,
        application_id=request.application_id,
        entity_type="lms_servicing_installment",
        entity_id=installment_request_id,
        status=response_data.schedule_status,
    )

    return success_response(
        request=api_request,
        data=response_data,
        message="LMS servicing installment created successfully.",
    )