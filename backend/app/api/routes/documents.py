import uuid

from fastapi import APIRouter, Depends, Request, HTTPException, File, UploadFile
from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.core.responses import success_response
from backend.app.core.security import require_roles
from backend.app.core.workflow_logging import log_workflow_event

from backend.app.models.document import Document
from backend.app.models.auth_user import AuthUser

from backend.app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
)
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.bank_analysis import BankAnalysisResponse
from backend.app.schemas.document_intelligence import DocumentIntelligenceResult, DocumentBankAnalysisAcceptance

from backend.app.services.audit_log_service import audit_log_service
from backend.app.services.document_service import document_service
from backend.app.services.document_intelligence_service import (
    document_intelligence_service,
)
from backend.app.services.pdf_text_extraction_service import (
    pdf_text_extraction_service,
)
from backend.app.services.document_extraction_review_service import (
    document_extraction_review_service,
)


router = APIRouter(
    prefix="/documents",
    tags=["Source Data Ingestion"],
)


@router.post(
    "",
    response_model=ApiResponse[DocumentResponse],
)
def create_document(
    document: DocumentCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    application_id = document.application_id

    log_workflow_event(
        workflow="document_creation",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="document_ingestion",
        entity_id=application_id,
    )

    try:
        result = document_service.create_document(
            db=db,
            document=document,
        )

    except Exception:
        log_workflow_event(
            workflow="document_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="document_ingestion",
            entity_id=application_id,
            error_code="DOCUMENT_CREATION_FAILED",
        )
        raise

    try:
        response_data = DocumentResponse.model_validate(result)
    except Exception:
        log_workflow_event(
            workflow="document_creation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="document_ingestion",
            entity_id=application_id,
            error_code="DOCUMENT_RESPONSE_VALIDATION_FAILED",
        )
        raise

    log_workflow_event(
        workflow="document_creation",
        event="completed",
        request=request,
        application_id=result.application_id,
        entity_type="document_ingestion",
        entity_id=application_id,
    )
    
    return success_response(
        request=request,
        data=response_data,
        message="Document data created successfully.",
    )


@router.post(
    "/{document_id}/extract-pdf",
    response_model=ApiResponse[DocumentIntelligenceResult],
)
async def extract_document_pdf(
    document_id: str,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    application_id = None

    log_workflow_event(
        workflow="document_intelligence",
        event="started",
        request=request,
        entity_type="document",
        entity_id=document_id,
    )

    try:
        document = db.get(Document, document_id)

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="DOCUMENT_NOT_FOUND",
            )

        application_id = document.application_id

        # Accept an ordinary PDF upload; the PDF parser will also verify
        # the actual file signature.
        filename = (file.filename or "").lower()
        content_type = (file.content_type or "").split(";")[0].strip().lower()

        if not (
            filename.endswith(".pdf")
            or content_type == "application/pdf"
        ):
            raise HTTPException(
                status_code=415,
                detail="DOCUMENT_PDF_REQUIRED",
            )

        pdf_bytes = await file.read(
            pdf_text_extraction_service.MAX_PDF_BYTES + 1
        )

        if len(pdf_bytes) > pdf_text_extraction_service.MAX_PDF_BYTES:
            raise HTTPException(
                status_code=413,
                detail="DOCUMENT_PDF_TOO_LARGE",
            )

        source_text = pdf_text_extraction_service.extract_text(pdf_bytes)

        result = document_intelligence_service.extract_and_validate(
            db=db,
            document_id=document_id,
            source_text=source_text,
        )

        log_workflow_event(
            workflow="document_intelligence",
            event="completed",
            request=request,
            application_id=result.application_id,
            entity_type="document",
            entity_id=result.document_id,
        )

        return success_response(
            request=request,
            data=result,
            message=(
                "PDF text extracted and structured document analysis completed. "
                "Document verification status was not changed."
            ),
        )

    except HTTPException as exc:
        db.rollback()

        log_workflow_event(
            workflow="document_intelligence",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="document",
            entity_id=document_id,
            error_code=str(exc.detail),
        )
        raise

    except ValueError as exc:
        db.rollback()
        error_code = str(exc)

        log_workflow_event(
            workflow="document_intelligence",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="document",
            entity_id=document_id,
            error_code=error_code,
        )

        if error_code in {
            "DOCUMENT_NOT_FOUND",
            "APPLICATION_NOT_FOUND",
        }:
            status_code = 404
        elif error_code == "DOCUMENT_PDF_TOO_LARGE":
            status_code = 413
        else:
            status_code = 422

        raise HTTPException(
            status_code=status_code,
            detail=error_code,
        ) from exc

    except RuntimeError as exc:
        db.rollback()
        error_code = str(exc)

        log_workflow_event(
            workflow="document_intelligence",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="document",
            entity_id=document_id,
            error_code=error_code,
        )

        status_code = (
            503
            if error_code == "GENAI_PROVIDER_NOT_CONFIGURED"
            else 502
        )

        raise HTTPException(
            status_code=status_code,
            detail=error_code,
        ) from exc

    except Exception:
        db.rollback()

        log_workflow_event(
            workflow="document_intelligence",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="document",
            entity_id=document_id,
            error_code="DOCUMENT_INTELLIGENCE_FAILED",
        )
        raise

    finally:
        await file.close()

@router.post(
    "/{document_id}/accept-bank-analysis",
    response_model=ApiResponse[BankAnalysisResponse],
)
def accept_document_bank_analysis(
    document_id: str,
    review: DocumentBankAnalysisAcceptance,
    request: Request,
    db: Session = Depends(get_db),
        current_user: AuthUser = Depends(
        require_roles(
            "ADMIN",
            "CREDIT_ANALYST",
            "CREDIT_OFFICER",
            "OPERATIONS",
            "RISK",
        )
    ),
):
    log_workflow_event(
        workflow="document_extraction_acceptance",
        event="started",
        request=request,
        entity_type="document",
        entity_id=document_id,
    )

    if review.reviewer_id.strip() != current_user.username:
        raise HTTPException(
            status_code=403,
            detail="REVIEWER_IDENTITY_MISMATCH",
        )

    try:
        result = document_extraction_review_service.accept(
            db=db,
            document_id=document_id,
            review=review,
        )

        response_data = BankAnalysisResponse.model_validate(result)

        audit_log_service.log(
            db=db,
            audit_log_id=f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            application_id=result.application_id,
            actor_type="HUMAN_REVIEWER",
            actor_reference=review.reviewer_id.strip(),
            action="DOCUMENT_BANK_ANALYSIS_ACCEPTED",
            entity_type="BANK_ANALYSIS",
            entity_reference=result.bank_analysis_id,
            description=(
                "Reviewer accepted extracted bank-statement fields "
                "into a new bank-analysis version. The source remains "
                "UNVERIFIED pending its separate verification workflow."
            ),
            previous_state="EXTRACTED_DATA_REVIEW",
            new_state="BANK_ANALYSIS_CREATED_UNVERIFIED",
        )

        db.commit()
        db.refresh(result)

    except ValueError as exc:
        db.rollback()
        error_code = str(exc)

        log_workflow_event(
            workflow="document_extraction_acceptance",
            event="failed",
            request=request,
            entity_type="document",
            entity_id=document_id,
            error_code=error_code,
        )

        if error_code in {
            "DOCUMENT_NOT_FOUND",
            "APPLICATION_NOT_FOUND",
        }:
            status_code = 404
        elif error_code in {
            "DOCUMENT_EXTRACTION_NOT_AVAILABLE",
            "DOCUMENT_EXTRACTION_REFERENCE_MISMATCH",
            "DOCUMENT_FIELD_CONFLICT_ACKNOWLEDGEMENT_REQUIRED",
            "DOCUMENT_CONFLICT_ACKNOWLEDGEMENT_INVALID",
        }:
            status_code = 409
        else:
            status_code = 422

        raise HTTPException(
            status_code=status_code,
            detail=error_code,
        ) from exc

    except Exception as exc:
        db.rollback()

        log_workflow_event(
            workflow="document_extraction_acceptance",
            event="failed",
            request=request,
            entity_type="document",
            entity_id=document_id,
            error_code="DOCUMENT_EXTRACTION_ACCEPTANCE_FAILED",
        )
        raise

    log_workflow_event(
        workflow="document_extraction_acceptance",
        event="completed",
        request=request,
        application_id=result.application_id,
        entity_type="bank_analysis",
        entity_id=result.bank_analysis_id,
    )

    return success_response(
        request=request,
        data=response_data,
        message=(
            "Reviewed document fields accepted into a new bank-analysis "
            "version. Previously stored bank-analysis records were retained."
        ),
    )