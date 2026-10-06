from fastapi import APIRouter, Request

from backend.app.core.responses import success_response
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
    result = lms_service.create_loan_account(request)

    response_data = LMSSanctionResponse.model_validate(result)

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
    result = lms_service.update_loan_status(request)

    response_data = LMSLoanStatusResponse.model_validate(result)

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
    result = lms_service.create_repayment_schedule(request)

    response_data = LMSRepaymentScheduleResponse.model_validate(result)

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
    result = lms_service.create_servicing_installment(request)

    response_data = LMSServicingInstallmentResponse.model_validate(result)

    return success_response(
        request=api_request,
        data=response_data,
        message="LMS servicing installment created successfully.",
    )