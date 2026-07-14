"""Auth dependency: decodes the JWT, sets TenantContext/CurrentUserContext
for the rest of the request, and exposes the decoded claims so
access_control.require_permission can check them without another query."""
from __future__ import annotations

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.settings import get_settings
from core.application.exceptions import UnauthorizedException
from core.infrastructure.security import decode_token
from core.infrastructure.tenant_context import CurrentUserContext, TenantContext

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_claims(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme)) -> dict:
    if credentials is None:
        raise UnauthorizedException("Missing bearer token.")

    settings = get_settings()
    try:
        claims = decode_token(credentials.credentials, secret_key=settings.jwt_secret)
    except ValueError as exc:
        raise UnauthorizedException(str(exc)) from exc

    if claims.get("type") != "access":
        raise UnauthorizedException("Provided token is not an access token.")

    user_id = uuid.UUID(claims["sub"])
    tenant_id = uuid.UUID(claims["tenant_id"]) if claims.get("tenant_id") else None

    CurrentUserContext.set(user_id)
    TenantContext.set(tenant_id)

    return claims


async def get_current_user_id(claims: dict = Depends(get_current_claims)) -> uuid.UUID:
    return uuid.UUID(claims["sub"])
