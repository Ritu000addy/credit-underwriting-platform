from datetime import datetime, timezone
from typing import Any, TypeVar

from fastapi import Request

from backend.app.core.request_context import (
    get_request_id,
)
from backend.app.schemas.common import (
    ApiError,
    ApiMeta,
    ApiResponse,
)


T = TypeVar("T")


def _build_meta(request: Request) -> ApiMeta:
    return ApiMeta(
        request_id=get_request_id(request),
        timestamp=datetime.now(timezone.utc),
        path=request.url.path,
    )


def success_response(
    *,
    request: Request,
    data: T,
    message: str,
) -> ApiResponse[T]:
    return ApiResponse(
        success=True,
        message=message,
        data=data,
        error=None,
        meta=_build_meta(request),
    )


def error_response(
    *,
    request: Request,
    code: str,
    message: str,
    details: Any | None = None,
) -> ApiResponse[None]:
    return ApiResponse(
        success=False,
        message=message,
        data=None,
        error=ApiError(
            code=code,
            details=details,
        ),
        meta=_build_meta(request),
    )