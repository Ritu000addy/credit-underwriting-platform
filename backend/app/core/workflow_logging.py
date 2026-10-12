import logging
from typing import Literal

from fastapi import Request

from backend.app.core.request_context import get_request_id

WorkflowEvent = Literal["started", "completed", "failed"]

def log_workflow_event(
    *,
    workflow: str,
    event: WorkflowEvent,
    request: Request,
    application_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    status: str | None = None,
    error_code: str | None = None,
) -> None:
    """Log a workflow lifecycle event without borrower payloads."""

    if event == "failed":
        level = logging.WARNING if error_code else logging.ERROR
    else:
        level = logging.INFO

    logger = logging.getLogger("backend.workflow")

    logger.log(
        level,
        "workflow_event request_id=%s workflow=%s event=%s "
        "application_id=%s entity_type=%s entity_id=%s "
        "status=%s error_code=%s",
        get_request_id(request),
        workflow,
        event,
        application_id or "-",
        entity_type or "-",
        entity_id or "-",
        status or "-",
        error_code or "-",
    )