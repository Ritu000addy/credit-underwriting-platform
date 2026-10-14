import re
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.models.bank_analysis import BankAnalysis
from backend.app.models.bureau_report import BureauReport
from backend.app.services.audit_log_service import audit_log_service


class SourceEvidenceVerificationService:

    @staticmethod
    def _validate_reviewer_id(reviewer_id: str | None) -> str:
        if not isinstance(reviewer_id, str):
            raise ValueError("REVIEWER_REQUIRED")

        reviewer_reference = reviewer_id.strip()

        if not reviewer_reference:
            raise ValueError("REVIEWER_REQUIRED")

        if not re.fullmatch(
            r"[A-Za-z0-9_.@-]{2,100}",
            reviewer_reference,
        ):
            raise ValueError("REVIEWER_ID_INVALID")

        return reviewer_reference

    def _verify_record(
        self,
        db: Session,
        *,
        model,
        id_attribute: str,
        record_id: str,
        not_found_code: str,
        entity_type: str,
        action: str,
        reviewer_id: str,
    ):
        reviewer_reference = self._validate_reviewer_id(reviewer_id)

        try:
            record = (
                db.query(model)
                .filter(
                    getattr(model, id_attribute) == record_id
                )
                .with_for_update()
                .one_or_none()
            )

            if record is None:
                raise ValueError(not_found_code)

            previous_status = (
                record.verification_status or ""
            ).strip().upper()

            # Only an unverified record can transition to VERIFIED.
            if previous_status != "UNVERIFIED":
                raise ValueError(
                    "SOURCE_EVIDENCE_NOT_ELIGIBLE_FOR_VERIFICATION"
                )

            verified_at = datetime.utcnow()

            record.verification_status = "VERIFIED"
            record.verified_by = reviewer_reference
            record.verified_at = verified_at

            audit_log_service.log(
                db=db,
                audit_log_id=f"AUDIT-{uuid4().hex[:12].upper()}",
                application_id=record.application_id,
                actor_type="HUMAN_REVIEWER",
                actor_reference=reviewer_reference,
                action=action,
                entity_type=entity_type,
                entity_reference=record_id,
                description=(
                    f"{entity_type} verification recorded "
                    "through the controlled reviewer service."
                ),
                previous_state=previous_status,
                new_state="VERIFIED",
            )

            # Record status and audit event atomically.
            db.commit()
            db.refresh(record)

            return record

        except Exception:
            db.rollback()
            raise

    def verify_bureau_report(
        self,
        db: Session,
        bureau_report_id: str,
        reviewer_id: str,
    ) -> BureauReport:
        return self._verify_record(
            db=db,
            model=BureauReport,
            id_attribute="bureau_report_id",
            record_id=bureau_report_id,
            not_found_code="BUREAU_REPORT_NOT_FOUND",
            entity_type="BUREAU_REPORT",
            action="BUREAU_REPORT_VERIFIED",
            reviewer_id=reviewer_id,
        )

    def verify_bank_analysis(
        self,
        db: Session,
        bank_analysis_id: str,
        reviewer_id: str,
    ) -> BankAnalysis:
        return self._verify_record(
            db=db,
            model=BankAnalysis,
            id_attribute="bank_analysis_id",
            record_id=bank_analysis_id,
            not_found_code="BANK_ANALYSIS_NOT_FOUND",
            entity_type="BANK_ANALYSIS",
            action="BANK_ANALYSIS_VERIFIED",
            reviewer_id=reviewer_id,
        )


source_evidence_verification_service = (
    SourceEvidenceVerificationService()
)