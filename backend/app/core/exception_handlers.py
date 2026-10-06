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


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    response = error_response(
        request=request,
        code="REQUEST_VALIDATION_ERROR",
        message="Request validation failed.",
        details=exc.errors(),
    )

    return JSONResponse(
        status_code=422,
        content=response.model_dump(mode="json"),
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

    response = error_response(
        request=request,
        code="HTTP_ERROR",
        message=message,
        details=details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
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
    )