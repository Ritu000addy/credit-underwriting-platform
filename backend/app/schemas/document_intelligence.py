from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentExtractionRequest(BaseModel):
    # Text obtained from the document by an upstream text extraction/OCR step.
    source_text: str = Field(min_length=20, max_length=10000)


class ExtractedDocumentField(BaseModel):
    value: str | int | float | bool | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: str | None = None


class DocumentFieldConflict(BaseModel):
    field_name: str
    conflict_type: Literal[
        "EVIDENCE_NOT_FOUND",
        "BORROWER360_MISMATCH",
        "CONTRADICTORY_SOURCE_VALUES",
    ]
    document_value: str | int | float | bool | None = None
    borrower360_value: str | int | float | bool | None = None
    evidence: str | None = None
    message: str


class DocumentIntelligenceResult(BaseModel):
    status: Literal["EXTRACTION_COMPLETE", "NEEDS_REVIEW"]

    document_id: str
    application_id: str
    document_type: str
    analysis_reference: str

    fields: dict[str, ExtractedDocumentField] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    conflicts: list[DocumentFieldConflict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    provider: str
    model_name: str

    confidence_note: str = (
        "Model-reported confidence is not calibrated probability "
        "and does not constitute document verification."
    )

class DocumentBankAnalysisAcceptance(BaseModel):
    reviewer_id: str = Field(min_length=2, max_length=100)

    # The caller must explicitly confirm the review.
    confirmed: Literal[True]

    accepted_fields: list[
        Literal[
            "monthly_credits",
            "monthly_debits",
            "average_balance",
            "transaction_count",
            "bounce_count",
        ]
    ] = Field(min_length=1)

    # Required acknowledgements for conflicts in fields being accepted.
    acknowledged_conflicts: list[
        Literal[
            "monthly_credits",
            "monthly_debits",
            "average_balance",
            "transaction_count",
            "bounce_count",
        ]
    ] = Field(default_factory=list)