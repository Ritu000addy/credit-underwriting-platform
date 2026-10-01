from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.beneficiary_account import BeneficiaryAccount


class BeneficiaryValidationService:

    def validate_beneficiary(
        self,
        db: Session,
        beneficiary: BeneficiaryAccount,
    ) -> BeneficiaryAccount:

        if not beneficiary.account_holder_name:
            beneficiary.validation_status = "FAILED"
            beneficiary.failure_reason = "ACCOUNT_HOLDER_NAME_MISSING"

        elif not beneficiary.account_number_reference:
            beneficiary.validation_status = "FAILED"
            beneficiary.failure_reason = "ACCOUNT_NUMBER_REFERENCE_MISSING"

        elif not beneficiary.ifsc_code:
            beneficiary.validation_status = "FAILED"
            beneficiary.failure_reason = "IFSC_CODE_MISSING"

        elif not beneficiary.bank_name:
            beneficiary.validation_status = "FAILED"
            beneficiary.failure_reason = "BANK_NAME_MISSING"

        else:
            beneficiary.validation_status = "VALIDATED"
            beneficiary.validation_reference = (
                f"VAL-{beneficiary.beneficiary_id}"
            )
            beneficiary.failure_reason = None
            beneficiary.validated_at = datetime.utcnow()

        db.commit()
        db.refresh(beneficiary)

        return beneficiary


beneficiary_validation_service = BeneficiaryValidationService()