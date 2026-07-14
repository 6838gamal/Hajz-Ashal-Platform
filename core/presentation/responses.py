"""Unified API response envelope used by every Module's routers."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ApiMeta(BaseModel):
    request_id: str | None = None
    page: int | None = None
    page_size: int | None = None
    total: int | None = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ApiError | None = None
    meta: ApiMeta = ApiMeta()

    @classmethod
    def ok(cls, data: T, meta: ApiMeta | None = None) -> "ApiResponse[T]":
        return cls(success=True, data=data, error=None, meta=meta or ApiMeta())

    @classmethod
    def fail(cls, error: ApiError, meta: ApiMeta | None = None) -> "ApiResponse[T]":
        return cls(success=False, data=None, error=error, meta=meta or ApiMeta())
