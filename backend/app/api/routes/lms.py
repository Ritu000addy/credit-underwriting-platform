from fastapi import APIRouter

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


router = APIRouter(
    prefix="/lms",
    tags=["LMS Integration"],
)


@router.post(
    "/sanctions",
    response_model=LMSSanctionResponse,
)
def create_lms_loan_account(
    request: LMSSanctionRequest,
):
    return lms_service.create_loan_account(request)


@router.post(
    "/loan-status",
    response_model=LMSLoanStatusResponse,
)
def update_lms_loan_status(
    request: LMSLoanStatusRequest,
):
    return lms_service.update_loan_status(request)

@router.post(
    "/repayment-schedules",
    response_model=LMSRepaymentScheduleResponse,
)
def create_lms_repayment_schedule(
    request: LMSRepaymentScheduleRequest,
):
    return lms_service.create_repayment_schedule(request)

@router.post(
    "/servicing/installments",
    response_model=LMSServicingInstallmentResponse,
)
def create_lms_servicing_installment(
    request: LMSServicingInstallmentRequest,
):
    return lms_service.create_servicing_installment(request)