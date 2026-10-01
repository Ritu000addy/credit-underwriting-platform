from sqlalchemy.orm import Session

from backend.app.models.beneficiary_account import BeneficiaryAccount


class BeneficiaryService:

    def create_beneficiary(
        self,
        db: Session,
        beneficiary_id: str,
        application_id: str,
        account_holder_name: str,
        account_number_reference: str,
        ifsc_code: str,
        bank_name: str,
    ) -> BeneficiaryAccount:

        beneficiary = BeneficiaryAccount(
            beneficiary_id=beneficiary_id,
            application_id=application_id,
            account_holder_name=account_holder_name,
            account_number_reference=account_number_reference,
            ifsc_code=ifsc_code,
            bank_name=bank_name,
            validation_status="PENDING",
        )

        db.add(beneficiary)
        db.commit()
        db.refresh(beneficiary)

        return beneficiary


beneficiary_service = BeneficiaryService()