import json
import re
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from backend.app.models.bank_analysis import BankAnalysis
from backend.app.models.document import Document

from backend.app.schemas.bank_analysis import BankAnalysisCreate
from backend.app.schemas.document_intelligence import (
    DocumentBankAnalysisAcceptance,
    DocumentIntelligenceResult,
)

from backend.app.services.bank_analysis_service import bank_analysis_service

class DocumentExtractionReviewService:
    FIELD_MAP = {
        "monthly_credits": ("monthly_credits", "amount"),
        "monthly_debits": ("monthly_debits", "amount"),
        "average_balance": ("average_balance", "amount"),
        "transaction_count": ("transactions_count", "count"),
        "bounce_count": ("bounce_count", "count"),
    }

    @staticmethod
    def _parse_amount(value) -> Decimal:
        if isinstance(value, bool) or value is None:
            raise ValueError("DOCUMENT_FIELD_VALUE_INVALID")

        if isinstance(value, (int, float, Decimal)):
            try:
                number = Decimal(str(value))
            except (InvalidOperation, ValueError) as exc:
                raise ValueError("DOCUMENT_FIELD_VALUE_INVALID") from exc
        elif isinstance(value, str):
            cleaned = value.strip().replace(",", "")
            cleaned = cleaned.replace("₹", "")
            cleaned = re.sub(r"(?i)\bINR\b", "", cleaned)
            cleaned = re.sub(r"(?i)\bRS\.?\s*", "", cleaned).strip()

            if not re.fullmatch(
                r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)",
                cleaned,
            ):
                raise ValueError("DOCUMENT_FIELD_VALUE_INVALID")

            try:
                number = Decimal(cleaned)
            except InvalidOperation as exc:
                raise ValueError("DOCUMENT_FIELD_VALUE_INVALID") from exc
        else:
            raise ValueError("DOCUMENT_FIELD_VALUE_INVALID")

        if not number.is_finite():
            raise ValueError("DOCUMENT_FIELD_VALUE_INVALID")

        return number

    
    @classmethod
    def _parse_field_value(cls, field_name: str, value):
        mapping = cls.FIELD_MAP.get(field_name)
        if mapping is None:
            raise ValueError("DOCUMENT_FIELD_NOT_ACCEPTABLE")

        _, value_type = mapping
        number = cls._parse_amount(value)

        if value_type == "count":
            if number < 0 or number != number.to_integral_value():
                raise ValueError("DOCUMENT_FIELD_VALUE_INVALID")
            return int(number)

        if field_name in {"monthly_credits", "monthly_debits"} and number < 0:
            raise ValueError("DOCUMENT_FIELD_VALUE_INVALID")

        return number

    
    def accept(
        self,
        db: Session,
        document_id: str,
        review: DocumentBankAnalysisAcceptance,
    ) -> BankAnalysis:
        document = db.get(Document, document_id)
        if document is None:
            raise ValueError("DOCUMENT_NOT_FOUND")

        if document.document_type.strip().upper().replace("-", "_").replace(" ", "_") != "BANK_STATEMENT":
            raise ValueError("BANK_STATEMENT_DOCUMENT_REQUIRED")

        if not document.extracted_data or not document.analysis_reference:
            raise ValueError("DOCUMENT_EXTRACTION_NOT_AVAILABLE")

        try:
            extraction = DocumentIntelligenceResult.model_validate(
                json.loads(document.extracted_data)
            )
        except Exception as exc:
            raise ValueError("DOCUMENT_EXTRACTION_RESULT_INVALID") from exc

        if (
            extraction.document_id != document.document_id
            or extraction.application_id != document.application_id
            or extraction.analysis_reference != document.analysis_reference
            or not extraction.analysis_reference.startswith("DOC-INTEL-")
        ):
            raise ValueError("DOCUMENT_EXTRACTION_REFERENCE_MISMATCH")

        if not review.reviewer_id.strip():
            raise ValueError("DOCUMENT_REVIEWER_REQUIRED")

        selected_fields = list(review.accepted_fields)
        acknowledged = set(review.acknowledged_conflicts)

        if not acknowledged.issubset(set(selected_fields)):
            raise ValueError(
                "DOCUMENT_CONFLICT_ACKNOWLEDGEMENT_INVALID"
            )

        if len(selected_fields) != len(set(selected_fields)):
            raise ValueError("DUPLICATE_ACCEPTED_FIELDS")

        detected_mismatches = {
            conflict.field_name
            for conflict in extraction.conflicts
            if conflict.conflict_type == "BORROWER360_MISMATCH"
        }

        if not acknowledged.issubset(detected_mismatches):
            raise ValueError("DOCUMENT_CONFLICT_ACKNOWLEDGEMENT_INVALID")

        for field_name in selected_fields:
            extracted_field = extraction.fields.get(field_name)

            if (
                extracted_field is None
                or extracted_field.value is None
                or not extracted_field.evidence
            ):
                raise ValueError("DOCUMENT_FIELD_NOT_AVAILABLE")

            field_conflicts = [
                conflict
                for conflict in extraction.conflicts
                if conflict.field_name == field_name
            ]

            if any(
                conflict.conflict_type == "EVIDENCE_NOT_FOUND"
                for conflict in field_conflicts
            ):
                raise ValueError("DOCUMENT_FIELD_EVIDENCE_INVALID")

            if (
                field_name in detected_mismatches
                and field_name not in acknowledged
            ):
                raise ValueError(
                    "DOCUMENT_FIELD_CONFLICT_ACKNOWLEDGEMENT_REQUIRED"
                )

        current = (
            db.query(BankAnalysis)
            .filter(
                BankAnalysis.application_id == document.application_id
            )
            .order_by(BankAnalysis.analyzed_at.desc())
            .first()
        )

        values = {
            "monthly_credits": current.monthly_credits if current else None,
            "monthly_debits": current.monthly_debits if current else None,
            "average_balance": current.average_balance if current else None,
            "existing_emi": current.existing_emi if current else None,
            "bounce_count": current.bounce_count if current else None,
            "transactions_count": current.transactions_count if current else None,
            "income_trend": current.income_trend if current else None,
        }

        # Overwrite only explicitly accepted fields.
        for field_name in selected_fields:
            analysis_field, _ = self.FIELD_MAP[field_name]
            values[analysis_field] = self._parse_field_value(
                field_name,
                extraction.fields[field_name].value,
            )

        reviewer_id = re.sub(
            r"[^A-Za-z0-9_.@-]",
            "_",
            review.reviewer_id.strip(),
        )
        accepted_names = ",".join(sorted(selected_fields))

        reference = (
            f"DOC-INTEL={extraction.analysis_reference}"
            f"|DOC={document.document_id}"
            f"|REVIEWER={reviewer_id}"
            f"|FIELDS={accepted_names}"
        )

        bank_analysis_input = BankAnalysisCreate(
            application_id=document.application_id,
            monthly_credits=values["monthly_credits"],
            monthly_debits=values["monthly_debits"],
            average_balance=values["average_balance"],
            existing_emi=values["existing_emi"],
            bounce_count=values["bounce_count"],
            transactions_count=values["transactions_count"],
            income_trend=values["income_trend"],
            analysis_reference=reference,
        )

        return bank_analysis_service.create_analysis(
            db=db,
            analysis=bank_analysis_input,
        )


document_extraction_review_service = DocumentExtractionReviewService()