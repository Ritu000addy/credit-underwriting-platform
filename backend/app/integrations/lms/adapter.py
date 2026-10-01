from datetime import datetime
from uuid import uuid4

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


class LMSAdapter:

    def create_loan_account(
        self,
        request: LMSSanctionRequest,
    ) -> LMSSanctionResponse:
        """
        Development LMS adapter.

        This simulates the LMS response until the
        actual external LMS API contract is provided.
        """

        return LMSSanctionResponse(
            loan_account_id=f"LMS-LOAN-{uuid4().hex[:12].upper()}",
            application_id=request.application_id,
            sanction_id=request.sanction_id,
            loan_status="ACTIVE",
            created_at=datetime.utcnow(),
        )

    def create_repayment_schedule(
        self,
        request: LMSRepaymentScheduleRequest,
    ) -> LMSRepaymentScheduleResponse:
        """
        Development LMS adapter.

        Simulates repayment schedule creation in the LMS
        until the actual external LMS API contract is provided.
        """

        return LMSRepaymentScheduleResponse(
            repayment_schedule_id=f"LMS-SCHEDULE-{uuid4().hex[:12].upper()}",
            loan_account_id=request.loan_account_id,
            application_id=request.application_id,
            schedule_status="CREATED",
            created_at=datetime.utcnow(),
        )

    def create_servicing_installment(
        self,
        request: LMSServicingInstallmentRequest,
    ) -> LMSServicingInstallmentResponse:
        """
        Development LMS adapter.

        Simulates creation of a servicing installment in the LMS
        until the actual external LMS API contract is provided.
        """

        return LMSServicingInstallmentResponse(
            repayment_schedule_id=request.repayment_schedule_id,
            loan_account_id=request.loan_account_id,
            installment_number=request.installment_number,
            schedule_status="CREATED",
        )

    def update_loan_status(
        self,
        request: LMSLoanStatusRequest,
    ) -> LMSLoanStatusResponse:
        """
        Development LMS adapter.

        Simulates loan-status synchronization until the actual
        external LMS API/webhook contract is provided.
        """

        return LMSLoanStatusResponse(
            loan_account_id=request.loan_account_id,
            application_id=request.application_id,
            loan_status=request.loan_status,
            updated_at=datetime.utcnow(),
        )

lms_adapter = LMSAdapter()