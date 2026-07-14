"""Ambient Tenant Context (contextvars) - set once per request by
TenantMiddleware, then read implicitly by BaseRepository so it is
impossible to accidentally query across tenants."""
from __future__ import annotations

import uuid
from contextvars import ContextVar

_tenant_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[uuid.UUID | None] = ContextVar("current_user_id", default=None)


class TenantContext:
    @staticmethod
    def set(tenant_id: uuid.UUID | None) -> None:
        _tenant_id_ctx.set(tenant_id)

    @staticmethod
    def get() -> uuid.UUID | None:
        return _tenant_id_ctx.get()

    @staticmethod
    def require() -> uuid.UUID:
        tenant_id = _tenant_id_ctx.get()
        if tenant_id is None:
            raise RuntimeError("No tenant_id set in the current context")
        return tenant_id


class CurrentUserContext:
    @staticmethod
    def set(user_id: uuid.UUID | None) -> None:
        _user_id_ctx.set(user_id)

    @staticmethod
    def get() -> uuid.UUID | None:
        return _user_id_ctx.get()
