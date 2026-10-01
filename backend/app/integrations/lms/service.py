from backend.app.integrations.lms.adapter import lms_adapter
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


class LMSService:

    def create_loan_account(
        self,
        request: LMSSanctionRequest,
    ) -> LMSSanctionResponse:
        return lms_adapter.create_loan_account(request)

    def create_repayment_schedule(
        self,
        request: LMSRepaymentScheduleRequest,
    ) -> LMSRepaymentScheduleResponse:
        return lms_adapter.create_repayment_schedule(request)

    def create_servicing_installment(
        self,
        request: LMSServicingInstallmentRequest,
    ) -> LMSServicingInstallmentResponse:
        return lms_adapter.create_servicing_installment(request)

    def update_loan_status(
        self,
        request: LMSLoanStatusRequest,
    ) -> LMSLoanStatusResponse:
        return lms_adapter.update_loan_status(request)

lms_service = LMSService()