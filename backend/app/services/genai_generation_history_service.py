
import logging
import os
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.genai_generation_history import (
    GenAIGenerationHistory,
)
from backend.app.models.loan_application import LoanApplication


logger = logging.getLogger("backend.workflow")

PROMPT_VERSION = "genai-underwriting-v1"


def record_generation(
    db: Session,
    *,
    application_id: str | None,
    generation_type: str,
    status: str,
    request_reference: str | None,
    duration_ms: int | None = None,
    model_name: str | None = None,
    model_version: str | None = None,
    validation_status: str | None = None,
    error_code: str | None = None,
) -> None:
    """Persist safe metadata about one GenAI generation attempt."""

    # Direct function calls in existing unit tests do not receive
    # FastAPI-injected database sessions.
    if not hasattr(db, "add") or not hasattr(db, "commit"):
        return

    provider = os.getenv("GENAI_PROVIDER", "NONE").upper()

    if model_name and model_name.startswith("LLM-"):
        provider = model_name.removeprefix("LLM-").upper()
    elif model_name and model_name.startswith("DEV-RULE-BASED-GENAI"):
        provider = "NONE"

        history_application_id = application_id

    if application_id:
        application_exists = db.scalar(
            select(LoanApplication.application_id).where(
                LoanApplication.application_id == application_id
            )
        )

        if application_exists is None:
            logger.warning(
                "genai_history_application_not_found "
                "application_id=%s; storing history without application link",
                application_id,
            )
            history_application_id = None

    record = GenAIGenerationHistory(
        generation_id=f"GENAI-{uuid.uuid4().hex}",
        application_id=history_application_id,
        generation_type=generation_type,
        status=status,
        provider=provider,
        model_name=model_name,
        model_version=model_version,
        prompt_version=PROMPT_VERSION,
        duration_ms=duration_ms,
        validation_status=validation_status,
        error_code=error_code,
        request_reference=request_reference,
        generation_metadata=None,
    )

    try:
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "genai_generation_history_persistence_failed "
            "application_id=%s generation_type=%s",
            application_id,
            generation_type,
        )
        raise
