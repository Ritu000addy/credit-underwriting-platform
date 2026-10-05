from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.app.models.agreement import Agreement
from backend.app.models.mandate import Mandate
from backend.app.models.sanction import Sanction
from backend.app.models.beneficiary_account import BeneficiaryAccount

class DisbursementEligibilityService:

    def check_eligibility(
        self,
        db: Session,
        application_id: str,
        sanction_id: str,
        disbursement_amount: Decimal,
        beneficiary_reference: str | None,
    ) -> dict:

        reasons: list[str] = []

        # 1. Validate sanction
        sanction = db.get(Sanction, sanction_id)

        if sanction is None:
            reasons.append("SANCTION_NOT_FOUND")
        else:
            if sanction.application_id != application_id:
                reasons.append("SANCTION_APPLICATION_MISMATCH")

            if sanction.sanction_status != "APPROVED":
                reasons.append("SANCTION_NOT_APPROVED")

            if (
                sanction.expires_at is not None
                and sanction.expires_at < datetime.utcnow()
            ):
                reasons.append("SANCTION_EXPIRED")

            if disbursement_amount > sanction.sanctioned_amount:
                reasons.append("AMOUNT_EXCEEDS_SANCTION")

        # 2. Validate agreement
        signed_agreement = (
            db.query(Agreement)
            .filter(
                Agreement.application_id == application_id,
                Agreement.sanction_id == sanction_id,
                Agreement.agreement_status == "COMPLETED",
                Agreement.esign_status == "SIGNED",
            )
            .first()
        )

        if signed_agreement is None:
            reasons.append("AGREEMENT_NOT_COMPLETED")

        # 3. Validate mandate
        completed_mandate = (
            db.query(Mandate)
            .filter(
                Mandate.application_id == application_id,
                Mandate.status == "COMPLETED",
            )
            .first()
        )

        if completed_mandate is None:
            reasons.append("MANDATE_NOT_COMPLETED")

        # 4. Validate beneficiary account

        if not beneficiary_reference:
            reasons.append("BENEFICIARY_REFERENCE_REQUIRED")
        else:
            validated_beneficiary = (
                db.query(BeneficiaryAccount)
                .filter(
                    BeneficiaryAccount.beneficiary_id == beneficiary_reference,
                    BeneficiaryAccount.application_id == application_id,
                    BeneficiaryAccount.validation_status == "VALIDATED",
                )
                .first()
            )

            if validated_beneficiary is None:
                reasons.append("BENEFICIARY_NOT_VALIDATED")

        eligible = len(reasons) == 0

        return {
            "eligible": eligible,
            "application_id": application_id,
            "sanction_id": sanction_id,
            "disbursement_amount": disbursement_amount,
            "reasons": reasons,
        }


disbursement_eligibility_service = DisbursementEligibilityService()