from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    details: Any | None = None


class ApiMeta(BaseModel):
    request_id: str | None = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    path: str | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None
    error: ApiError | None = None
    meta: ApiMeta


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginationMeta