from anyio.streams.memory import MemoryObjectStreamStatistics
from backend.app.schemas.application import ApplicationCreate
from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.completeness import CompletenessResult

class CompletenessChecker:

    def check(
        self,
        application: ApplicationCreate,
        borrower: Borrower360,
    ) -> CompletenessResult:

        missing_fields: list[str] = []

        # Application-level checks

        if not application.application_id:
            missing_fields.append("application_id")

        if not application.customer_id:
            missing_fields.append("customer_id")

        if application.requested_amount is None:
            missing_fields.append("requested_amount")

        if application.loan_tenure_months is None:
            missing_fields.append("loan_tenure_months")
        
        # Borrower 360 domain checks
        if borrower.kyc is None:
            missing_fields.append("kyc")

        if borrower.credit_bureau is None:
            missing_fields.append("credit_bureau")

        if borrower.bank_cash_flow is None:
            missing_fields.append("bank_cash_flow")

        if borrower.employment_business is None:
            missing_fields.append("employment_business")

        if borrower.internal_history is None:
            missing_fields.append("internal_history")
        
        if borrower.device_behaviour is None:
            missing_fields.append("device_behavior")

        if borrower.documents is None:
            missing_fields.append("documents")

        status = "COMPLETE" if not missing_fields else "INCOMPLETE"

        return CompletenessResult(
            status= status,
            missing_fields=missing_fields
        )

completeness_checker = CompletenessChecker()