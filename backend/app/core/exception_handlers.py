import logging
import uuid
from datetime import datetime, timezone

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    if request_id:
        return request_id

    request_id = (
        f"REQ-{uuid.uuid4().hex[:12].upper()}"
    )

    request.state.request_id = request_id

    return request_id


def build_error_response(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details=None,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": message,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
            "request_id": get_request_id(request),
            "path": request.url.path,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return build_error_response(
        request=request,
        status_code=422,
        code="REQUEST_VALIDATION_ERROR",
        message="Request validation failed.",
        details=exc.errors(),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    if isinstance(exc.detail, str):
        message = exc.detail
        details = None
    else:
        message = "Request failed."
        details = exc.detail

    return build_error_response(
        request=request,
        status_code=exc.status_code,
        code="HTTP_ERROR",
        message=message,
        details=details,
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
):
    logger.exception(
        "Database integrity error. request_id=%s",
        get_request_id(request),
        exc_info=exc,
    )

    return build_error_response(
        request=request,
        status_code=409,
        code="DATABASE_CONSTRAINT_VIOLATION",
        message="Database integrity constraint violated.",
        details=None,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled application exception. request_id=%s",
        get_request_id(request),
        exc_info=exc,
    )

    return build_error_response(
        request=request,
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal error occurred.",
        details=None,
    )