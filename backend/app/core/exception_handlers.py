import re
import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.request_context import (
    get_request_id,
)
from backend.app.core.responses import (
    error_response,
)


logger = logging.getLogger(__name__)

HTTP_STATUS_ERROR_CODES = {
    400: ("BAD_REQUEST", "The request could not be processed."),
    401: ("AUTHENTICATION_REQUIRED", "Authentication is required."),
    403: ("ACCESS_FORBIDDEN", "Access to this resource is forbibben"),
    404: ("RESOURCE_NOT_FOUND", "The requested resource was not found."),
    405: ("METHOD_NOT_ALLOWED", "The HTTP method is not allowed."),
    409: ("RESOURCE_CONFLICT", "The request conflicts with the current resource state."),
    422: ("BUSINESS_RULE_VIOLATION", "The request violates a business rule."),
    429: ("RATE_LIMITED", "Too many requests."),
    500: ("INTERNAL_SERVER_ERROR", "An unexpected internal server error occurred."),
    502: ("UPSTREAM_PROVIDER_ERROR", "An upstream provider request failed."),
    503: ("SERVICE_UNAVAILABLE", "The service is temporarily unavailable."),
}

def _extract_domain_error_code(message: str) -> str | None:
    """Extract a stable code from a domain error, if present."""
    candidate = message.partition(":")[0].strip()

    if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", candidate):
        return candidate

    return None

async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):

    validation_details = [
        {
            "loc": list(error.get("loc", [])),
            "msg": error.get("msg", "Invalid value."),
            "type": error.get("type", "validation_error"),
        }
        for error in exc.errors()
    ]

    response = error_response(
        request=request,
        code="REQUEST_VALIDATION_ERROR",
        message="Request validation failed.",
        details=validation_details,
    )

    return JSONResponse(
        status_code=422,
        content=response.model_dump(mode="json"),
        headers={
            "X-Request-ID": get_request_id(request),
        },
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    default_code, default_message = HTTP_STATUS_ERROR_CODES.get(
        exc.status_code,
        ("HTTP_ERROR", "Request failed."),
    )

    if isinstance(exc.detail, str):
        message = exc.detail
        details = None
    else:
        message = default_message
        details = exc.detail

    code = _extract_domain_error_code(message) or default_code

    if request.url.path.startswith("/genai-underwriting"):
        if exc.status_code == 502:
            if message == (
                "The GenAI provider returned an invalid structured response."
            ):
                code = "GENAI_INVALID_STRUCTURED_RESPONSE"
            elif message == "GenAI generation failed.":
                code = "GENAI_GENERATION_FAILED"
            elif code == "UPSTREAM_PROVIDER_ERROR":
                code = "GENAI_PROVIDER_ERROR"

    response = error_response(
        request=request,
        code=code,
        message=message,
        details=details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
        headers={
            "X-Request-ID": get_request_id(request),
        },
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

    response = error_response(
        request=request,
        code="DATABASE_CONSTRAINT_VIOLATION",
        message="Database integrity constraint violated.",
        details=None,
    )

    return JSONResponse(
        status_code=409,
        content=response.model_dump(mode="json"),
        headers={
            "X-Request-ID": get_request_id(request),
        },
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

    response = error_response(
        request=request,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal error occurred.",
        details=None,
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(mode="json"),
        headers={
            "X-Request-ID": get_request_id(request),
        },
    )