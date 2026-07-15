"""Auth dependency for the platform-superadmin surface. Deliberately
separate from `modules.identity.presentation.dependencies.get_current_claims`
- it never touches TenantContext (a platform admin isn't scoped to any
tenant), and it rejects any token that isn't explicitly minted with
scope="platform_admin" (see core/infrastructure/security.py)."""
from __future__ import annotations

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.settings import get_settings
from core.application.exceptions import ForbiddenException, UnauthorizedException
from core.infrastructure.security import decode_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_platform_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    if credentials is None:
        raise UnauthorizedException("Missing bearer token.")

    settings = get_settings()
    try:
        claims = decode_token(credentials.credentials, secret_key=settings.jwt_secret)
    except ValueError as exc:
        raise UnauthorizedException(str(exc)) from exc

    if claims.get("type") != "access" or claims.get("scope") != "platform_admin":
        raise ForbiddenException("This endpoint requires a platform-admin session.")

    return {"admin_id": uuid.UUID(claims["sub"])}
