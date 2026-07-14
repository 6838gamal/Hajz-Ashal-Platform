"""Centralized Exception -> HTTP mapping so every Module's routers can just
raise/return without duplicating try/except blocks."""
from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.application.exceptions import (
    ConflictException,
    DomainException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    UsageLimitExceededException,
    ValidationException,
)
from core.presentation.responses import ApiError, ApiMeta, ApiResponse

_STATUS_BY_EXCEPTION = {
    NotFoundException: 404,
    ConflictException: 409,
    ValidationException: 422,
    UnauthorizedException: 401,
    ForbiddenException: 403,
    UsageLimitExceededException: 402,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def handle_domain_exception(request: Request, exc: DomainException):
        status_code = 400
        for exc_type, code in _STATUS_BY_EXCEPTION.items():
            if isinstance(exc, exc_type):
                status_code = code
                break
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        body = ApiResponse.fail(
            ApiError(code=exc.code, message=exc.message, details=exc.details),
            meta=ApiMeta(request_id=request_id),
        )
        return JSONResponse(status_code=status_code, content=body.model_dump())

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        body = ApiResponse.fail(
            ApiError(code="INTERNAL_ERROR", message="Unexpected server error."),
            meta=ApiMeta(request_id=request_id),
        )
        return JSONResponse(status_code=500, content=body.model_dump())
