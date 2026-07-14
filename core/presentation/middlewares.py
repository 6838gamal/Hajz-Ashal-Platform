"""Cross-cutting middlewares registered once in app/main.py."""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.infrastructure.tenant_context import CurrentUserContext, TenantContext


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Clears tenant/user context per-request. The actual tenant_id/user_id
    values are set inside the auth dependency (get_current_user) once the
    JWT is decoded, since that is the only point that has verified them."""

    async def dispatch(self, request: Request, call_next):
        TenantContext.set(None)
        CurrentUserContext.set(None)
        try:
            response = await call_next(request)
        finally:
            TenantContext.set(None)
            CurrentUserContext.set(None)
        return response
