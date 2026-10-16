import os
import time
import logging

from fastapi import APIRouter, HTTPException, Request, Response, Depends

from sqlalchemy.orm import Session

from backend.app.database import get_db

from backend.app.schemas.borrower360 import Borrower360
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.underwriting import UnderwritingResult
from backend.app.schemas.underwriting_report import UnderwritingReport
from backend.app.schemas.genai_underwriting import GenAIUnderwritingResult

from backend.app.services.genai_underwriting_service import (
    genai_underwriting_service,
)
from backend.app.services.underwriting_report_service import (
    underwriting_report_service,
)
from backend.app.services.genai_generation_history_service import (
    record_generation,
)

from backend.app.core.responses import success_response
from backend.app.core.request_context import get_request_id
from backend.app.core.workflow_logging import log_workflow_event

router = APIRouter(
    prefix="/genai-underwriting",
    tags=["GenAI Underwriting"],
)

logger = logging.getLogger("backend.workflow")


@router.post(
    "/analyze",
    response_model=ApiResponse[GenAIUnderwritingResult],
)
def analyze_underwriting(
    borrower: Borrower360,
    underwriting: UnderwritingResult,
    request: Request,
    db: Session = Depends(get_db),
):
    application_id = underwriting.application_id

    log_workflow_event(
        workflow="genai_underwriting_analysis",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="genai_underwriting",
        entity_id=application_id,
    )

    if borrower.customer_id != underwriting.customer_id:
        log_workflow_event(
            workflow="genai_underwriting_analysis",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="genai_underwriting",
            entity_id=application_id,
            error_code="CUSTOMER_ID_MISMATCH",
        )
        raise HTTPException(
            status_code=400,
            detail="Borrower and underwriting customer IDs do not match.",
        )

    if not borrower.customer_id or not application_id:
        log_workflow_event(
            workflow="genai_underwriting_analysis",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="genai_underwriting",
            entity_id=application_id,
            error_code="GENAI_REQUIRED_DATA_MISSING",
        )
        raise HTTPException(
            status_code=400,
            detail="Borrower and underwriting data are required.",
        )

    started_at = time.perf_counter()

    logger.info(
        "genai_underwriting_started request_id=%s application_id=%s",
        get_request_id(request),
        application_id,
    )

    try:
        result = genai_underwriting_service.generate(
            borrower=borrower,
            underwriting=underwriting,
        )

        response_data = GenAIUnderwritingResult.model_validate(result)

    except ValueError as exc:
        record_generation(
            db,
            application_id=application_id,
            generation_type="UNDERWRITING_ANALYSIS",
            status="FAILED",
            request_reference=get_request_id(request),
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            validation_status="FAILED",
            error_code="GENAI_UNDERWRITING_VALIDATION_FAILED",
        )
        log_workflow_event(
            workflow="genai_underwriting_analysis",
            event="failed",
            request=request,
             application_id=application_id,
            entity_type="genai_underwriting",
            entity_id=application_id,
            error_code="GENAI_UNDERWRITING_VALIDATION_FAILED",
        )

        logger.warning(
            "genai_underwriting_validation_failed "
            "request_id=%s application_id=%s error_type=%s",
            get_request_id(request),
            application_id,
            type(exc).__name__,
        )

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        error_code = str(exc).split(":", 1)[0]

        safe_error_code = (
            error_code
            if error_code in {
                "GENAI_INVALID_STRUCTURED_RESPONSE",
                "GENAI_GENERATION_FAILED",
            }
            else "GENAI_PROVIDER_ERROR"
        )

        record_generation(
            db,
            application_id=application_id,
            generation_type="UNDERWRITING_ANALYSIS",
            status="FAILED",
            request_reference=get_request_id(request),
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            validation_status="FAILED",
            error_code=safe_error_code,
        )

        log_workflow_event(
            workflow="genai_underwriting_analysis",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="genai_underwriting",
            entity_id=application_id,
            error_code=safe_error_code,
        )

        logger.error(
            "genai_underwriting_failed "
            "request_id=%s application_id=%s error_code=%s",
            get_request_id(request),
            application_id,
            safe_error_code,
        )

        if error_code == "GENAI_INVALID_STRUCTURED_RESPONSE":
            raise HTTPException(
                status_code=502,
                detail="The GenAI provider returned an invalid structured response.",
            ) from exc

        if error_code == "GENAI_GENERATION_FAILED":
            raise HTTPException(
                status_code=502,
                detail="GenAI generation failed.",
            ) from exc

        raise HTTPException(
            status_code=502,
            detail="GenAI provider error.",
        ) from exc

    except Exception:
        record_generation(
            db,
            application_id=application_id,
            generation_type="UNDERWRITING_ANALYSIS",
            status="FAILED",
            request_reference=get_request_id(request),
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            validation_status="FAILED",
            error_code="GENAI_UNDERWRITING_FAILED",
        )
        log_workflow_event(
            workflow="genai_underwriting_analysis",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="genai_underwriting",
            entity_id=application_id,
            error_code="GENAI_UNDERWRITING_FAILED",
        )
        raise

    record_generation(
        db,
        application_id=application_id,
        generation_type="UNDERWRITING_ANALYSIS",
        status="COMPLETED",
        request_reference=get_request_id(request),
        duration_ms=int((time.perf_counter() - started_at) * 1000),
        model_name=getattr(response_data, "model_name", None),
        model_version=getattr(response_data, "model_version", None),
        validation_status="PASSED",
    )

    response = success_response(
        request=request,
        data=response_data,
        message="GenAI underwriting analysis completed successfully.",
    )

    logger.info(
        "genai_generation_completed "
        "request_id=%s application_id=%s duration_ms=%.2f",
        get_request_id(request),
        application_id,
        (time.perf_counter() - started_at) * 1000,
    )

    log_workflow_event(
        workflow="genai_underwriting_analysis",
        event="completed",
        request=request,
        application_id=application_id,
        entity_type="genai_underwriting",
        entity_id=application_id,
    )

    return response


@router.post(
    "/report",
    response_model=ApiResponse[UnderwritingReport],
)
def generate_underwriting_report(
    borrower: Borrower360,
    underwriting: UnderwritingResult,
    request: Request,
    db: Session = Depends(get_db),
) -> ApiResponse[UnderwritingReport]:
    application_id = underwriting.application_id
    started_at = time.perf_counter()

    log_workflow_event(
        workflow="underwriting_report_generation",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="underwriting_report",
        entity_id=application_id,
    )

    if borrower.customer_id != underwriting.customer_id:
        log_workflow_event(
            workflow="underwriting_report_generation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="underwriting_report",
            entity_id=application_id,
            error_code="CUSTOMER_ID_MISMATCH",
        )
        raise HTTPException(
            status_code=422,
            detail="CUSTOMER_ID_MISMATCH",
        )

    try:
        genai_result = genai_underwriting_service.generate(
            borrower=borrower,
            underwriting=underwriting,
        )

        report = underwriting_report_service.generate(
            underwriting=underwriting,
            genai=genai_result,
        )

        response = success_response(
            data=report,
            message="Internal underwriting report generated successfully",
            request= request,
        )

    except ValueError as exc:
        record_generation(
            db,
            application_id=application_id,
            generation_type="UNDERWRITING_REPORT",
            status="FAILED",
            request_reference=get_request_id(request),
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            validation_status="FAILED",
            error_code="UNDERWRITING_REPORT_GENERATION_REJECTED",
        )
        log_workflow_event(
            workflow="underwriting_report_generation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="underwriting_report",
            entity_id=application_id,
            error_code="UNDERWRITING_REPORT_GENERATION_REJECTED",
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        error_code = str(exc)

        record_generation(
            db,
            application_id=application_id,
            generation_type="UNDERWRITING_REPORT",
            status="FAILED",
            request_reference=get_request_id(request),
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            validation_status="FAILED",
            error_code=(
                error_code.split(":", 1)[0]
                if error_code.startswith("GENAI_")
                else "UNDERWRITING_REPORT_GENERATION_FAILED"
            ),
        )

        is_provider_error = (
            error_code.startswith("GENAI_")
            or "PROVIDER" in error_code
        )

        log_workflow_event(
            workflow="underwriting_report_generation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="underwriting_report",
            entity_id=application_id,
            error_code=(
                "GENAI_REPORT_PROVIDER_FAILED"
                if is_provider_error
                else "UNDERWRITING_REPORT_GENERATION_FAILED"
            ),
        )

        if is_provider_error:
            raise HTTPException(
                status_code=502,
                detail=error_code,
            ) from exc

        raise HTTPException(
            status_code=500,
            detail="Internal underwriting report generation failed",
        ) from exc

    except Exception:
        record_generation(
            db,
            application_id=application_id,
            generation_type="UNDERWRITING_REPORT",
            status="FAILED",
            request_reference=get_request_id(request),
            duration_ms=int((time.perf_counter() - started_at) * 1000),
            validation_status="FAILED",
            error_code="UNDERWRITING_REPORT_GENERATION_FAILED",
        )
        log_workflow_event(
            workflow="underwriting_report_generation",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="underwriting_report",
            entity_id=application_id,
            error_code="UNDERWRITING_REPORT_GENERATION_FAILED",
        )
        raise

    
    record_generation(
        db,
        application_id=application_id,
        generation_type="UNDERWRITING_REPORT",
        status="COMPLETED",
        request_reference=get_request_id(request),
        duration_ms=int((time.perf_counter() - started_at) * 1000),
        model_name=getattr(genai_result, "model_name", None),
        model_version=getattr(genai_result, "model_version", None),
        validation_status="PASSED",
    )

    log_workflow_event(
        workflow="underwriting_report_generation",
        event="completed",
        request=request,
        application_id=application_id,
        entity_type="underwriting_report",
        entity_id=application_id,
    )

    return response


@router.post(
    "/report/markdown",
    response_class=Response,
)
def export_underwriting_report_markdown(
    report: UnderwritingReport,
    request: Request,
) -> Response:
    application_id = report.application_id

    log_workflow_event(
        workflow="underwriting_report_markdown_export",
        event="started",
        request=request,
        application_id=application_id,
        entity_type="underwriting_report",
        entity_id=application_id,
    )

    try:
        markdown = underwriting_report_service.to_markdown(report)

        response = Response(
            content=markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": (
                    'attachment; filename="underwriting-report.md"'
                )
            },
        )

    except Exception:
        log_workflow_event(
            workflow="underwriting_report_markdown_export",
            event="failed",
            request=request,
            application_id=application_id,
            entity_type="underwriting_report",
            entity_id=application_id,
            error_code="UNDERWRITING_REPORT_MARKDOWN_EXPORT_FAILED",
        )
        raise

    log_workflow_event(
        workflow="underwriting_report_markdown_export",
        event="completed",
        request=request,
        application_id=application_id,
        entity_type="underwriting_report",
        entity_id=application_id,
    )

    return response