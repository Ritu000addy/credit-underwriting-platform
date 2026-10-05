import uuid

from sqlalchemy.orm import Session

from backend.app.models.disbursement import Disbursement
from backend.app.models.internal_ledger import InternalLedger
from backend.app.services.bank_routing_service import bank_routing_service
from backend.app.services.internal_ledger_service import internal_ledger_service
from backend.app.services.audit_log_service import audit_log_service


class DisbursementRetryService:

    MAX_RETRY_ATTEMPTS = 3

    RETRYABLE_FAILURES = {
        "BANK_TIMEOUT",
        "BANK_TEMPORARY_UNAVAILABLE",
        "PROVIDER_TIMEOUT",
        "PROVIDER_TEMPORARY_ERROR",
    }

    NON_RETRYABLE_FAILURES = {
        "BANK_ACCOUNT_BLOCKED",
        "INVALID_BANK_ACCOUNT",
        "INVALID_IFSC",
        "BENEFICIARY_VALIDATION_FAILED",
    }

    def is_retryable(self, failure_reason: str | None) -> bool:
        if not failure_reason:
            return False

        return failure_reason in self.RETRYABLE_FAILURES

    def can_retry(
        self,
        db: Session,
        disbursement_id: str,
    ) -> dict:

        disbursement = db.get(Disbursement, disbursement_id)

        if disbursement is None:
            return {
                "eligible": False,
                "disbursement_id": disbursement_id,
                "reason": "DISBURSEMENT_NOT_FOUND",
            }

        if disbursement.status != "FAILED":
            return {
                "eligible": False,
                "disbursement_id": disbursement_id,
                "reason": "DISBURSEMENT_NOT_FAILED",
            }

        if not self.is_retryable(disbursement.failure_reason):
            return {
                "eligible": False,
                "disbursement_id": disbursement_id,
                "reason": "FAILURE_NOT_RETRYABLE",
            }

        if disbursement.retry_attempts >= self.MAX_RETRY_ATTEMPTS:
            return {
                "eligible": False,
                "disbursement_id": disbursement_id,
                "reason": "MAX_RETRY_ATTEMPTS_EXCEEDED",
            }

        return {
            "eligible": True,
            "disbursement_id": disbursement_id,
            "reason": None,
        }

    def retry_disbursement(
        self,
        db: Session,
        disbursement_id: str,
    ) -> dict:

        eligibility = self.can_retry(
            db=db,
            disbursement_id=disbursement_id,
        )

        if not eligibility["eligible"]:
            return eligibility

        disbursement = db.get(
            Disbursement,
            disbursement_id,
        )

        disbursement.retry_attempts += 1

        routing_result = bank_routing_service.route_disbursement(
            payment_provider=disbursement.payment_provider,
            disbursement_id=disbursement.disbursement_id,
        )

        if not routing_result.success:
            disbursement.status = "FAILED"
            disbursement.failure_reason = routing_result.failure_reason

            audit_log_service.log(
                db=db,
                audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
                application_id=disbursement.application_id,
                actor_type="SYSTEM",
                action="DISBURSEMENT_RETRY_FAILED",
                entity_type="DISBURSEMENT",
                entity_reference=disbursement.disbursement_id,
                description="Disbursement retry failed during bank routing",
                previous_state="FAILED",
                new_state="FAILED",
                request_reference=disbursement.disbursement_id,
            )

            db.commit()
            db.refresh(disbursement)

            return {
                "eligible": True,
                "retried": False,
                "disbursement_id": disbursement_id,
                "retry_attempts": disbursement.retry_attempts,
                "status": "FAILED",
                "reason": routing_result.failure_reason,
            }

        disbursement.status = "INITIATED"
        disbursement.bank_reference = routing_result.routing_reference
        disbursement.failure_reason = None

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=disbursement.application_id,
            actor_type="SYSTEM",
            action="DISBURSEMENT_RETRIED",
            entity_type="DISBURSEMENT",
            entity_reference=disbursement.disbursement_id,
            description="Disbursement retried successfully and re-initiated",
            previous_state="FAILED",
            new_state="INITIATED",
            request_reference=disbursement.disbursement_id,
        )

        db.commit()
        db.refresh(disbursement)

        # Ensure the internal ledger entry exists after a
        # successful retry, just as it does for normal initiation.
        existing_ledger_entry = db.query(InternalLedger).filter(
            InternalLedger.disbursement_id == disbursement.disbursement_id,
            InternalLedger.transaction_type == "DISBURSEMENT",
        ).first()

        if existing_ledger_entry is None:
            internal_ledger_service.create_disbursement_entry(
                db=db,
                ledger_id=f"LEDGER-{uuid.uuid4().hex[:12].upper()}",
                application_id=disbursement.application_id,
                disbursement_id=disbursement.disbursement_id,
                transaction_amount=disbursement.disbursement_amount,
                internal_reference=f"LEDGER-{disbursement.disbursement_id}",
            )

        db.refresh(disbursement)

        return {
            "eligible": True,
            "retried": True,
            "disbursement_id": disbursement_id,
            "retry_attempts": disbursement.retry_attempts,
            "status": "INITIATED",
            "bank_reference": disbursement.bank_reference,
            "reason": None,
        }


disbursement_retry_service = DisbursementRetryService()