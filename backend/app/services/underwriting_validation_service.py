from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.underwriting_validation import (
    UnderwritingValidationResponse,
)


class UnderwritingValidationService:

    def validate(
        self,
        borrower: Borrower360,
    ) -> UnderwritingValidationResponse:

        missing_data = []
        validation_errors = []

        kyc_complete = borrower.kyc is not None
        bureau_available = borrower.credit_bureau is not None
        bank_data_available = borrower.bank_cash_flow is not None
        employment_data_available = (
            borrower.employment_business is not None
        )
        internal_history_available = (
            borrower.internal_history is not None
        )
        device_behaviour_available = (
            borrower.device_behaviour is not None
        )
        documents_available = borrower.documents is not None

        if not kyc_complete:
            missing_data.append("KYC")

        if not bureau_available:
            missing_data.append("CREDIT_BUREAU")

        if not bank_data_available:
            missing_data.append("BANK_ANALYSIS")

        if not employment_data_available:
            missing_data.append("EMPLOYMENT_BUSINESS")

        if not internal_history_available:
            missing_data.append("INTERNAL_HISTORY")

        if not device_behaviour_available:
            missing_data.append("DEVICE_BEHAVIOUR")

        if not documents_available:
            missing_data.append("DOCUMENTS")

        if borrower.customer_id is None:
            validation_errors.append(
                "CUSTOMER_ID_MISSING"
            )

        if missing_data:
            completeness_status = "INCOMPLETE"
        elif validation_errors:
            completeness_status = "INVALID"
        else:
            completeness_status = "COMPLETE"

        return UnderwritingValidationResponse(
            application_id="",
            completeness_status=completeness_status,
            kyc_complete=kyc_complete,
            bureau_available=bureau_available,
            bank_data_available=bank_data_available,
            employment_data_available=employment_data_available,
            internal_history_available=internal_history_available,
            device_behaviour_available=device_behaviour_available,
            documents_available=documents_available,
            missing_data=missing_data,
            validation_errors=validation_errors,
        )


underwriting_validation_service = UnderwritingValidationService()