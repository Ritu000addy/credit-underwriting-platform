from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.policy_validation import (
    PolicyValidationResponse,
)


class PolicyValidationService:

    def validate(
        self,
        borrower: Borrower360,
        application_id: str,
    ) -> PolicyValidationResponse:

        policy_checks = []
        policy_failures = []
        manual_review_flags = []

        # KYC availability check
        kyc_available = borrower.kyc is not None

        policy_checks.append(
            {
                "policy": "KYC_AVAILABILITY",
                "status": "PASS" if kyc_available else "FAIL",
                "value": kyc_available,
            }
        )

        if not kyc_available:
            policy_failures.append("KYC_NOT_AVAILABLE")

        # Bureau availability check
        bureau_available = borrower.credit_bureau is not None

        policy_checks.append(
            {
                "policy": "BUREAU_AVAILABILITY",
                "status": "PASS" if bureau_available else "FAIL",
                "value": bureau_available,
            }
        )

        if not bureau_available:
            policy_failures.append("CREDIT_BUREAU_NOT_AVAILABLE")

        # Bank data availability check
        bank_available = borrower.bank_cash_flow is not None

        policy_checks.append(
            {
                "policy": "BANK_DATA_AVAILABILITY",
                "status": "PASS" if bank_available else "FAIL",
                "value": bank_available,
            }
        )

        if not bank_available:
            policy_failures.append("BANK_DATA_NOT_AVAILABLE")

        # Employment / business availability check
        employment_available = (
            borrower.employment_business is not None
        )

        policy_checks.append(
            {
                "policy": "EMPLOYMENT_BUSINESS_AVAILABILITY",
                "status": (
                    "PASS"
                    if employment_available
                    else "FAIL"
                ),
                "value": employment_available,
            }
        )

        if not employment_available:
            policy_failures.append(
                "EMPLOYMENT_BUSINESS_NOT_AVAILABLE"
            )

        # Internal history availability check
        internal_history_available = (
            borrower.internal_history is not None
        )

        policy_checks.append(
            {
                "policy": "INTERNAL_HISTORY_AVAILABILITY",
                "status": (
                    "PASS"
                    if internal_history_available
                    else "FAIL"
                ),
                "value": internal_history_available,
            }
        )

        # Device / behaviour availability check
        device_available = (
            borrower.device_behaviour is not None
        )

        policy_checks.append(
            {
                "policy": "DEVICE_BEHAVIOUR_AVAILABILITY",
                "status": (
                    "PASS"
                    if device_available
                    else "FAIL"
                ),
                "value": device_available,
            }
        )

        if not device_available:
            manual_review_flags.append(
                "DEVICE_BEHAVIOUR_NOT_AVAILABLE"
            )

        # Document availability check
        documents_available = borrower.documents is not None

        policy_checks.append(
            {
                "policy": "DOCUMENT_AVAILABILITY",
                "status": (
                    "PASS"
                    if documents_available
                    else "FAIL"
                ),
                "value": documents_available,
            }
        )

        if not documents_available:
            manual_review_flags.append(
                "DOCUMENTS_NOT_AVAILABLE"
            )

        # Overall policy status
        if policy_failures:
            policy_status = "FAIL"
        elif manual_review_flags:
            policy_status = "REFER"
        else:
            policy_status = "PASS"

        return PolicyValidationResponse(
            application_id=application_id,
            policy_status=policy_status,
            policy_checks=policy_checks,
            policy_failures=policy_failures,
            manual_review_flags=manual_review_flags,
            policy_version="POL-2026.09",
        )


policy_validation_service = PolicyValidationService()