"""`require_permission` guards routes using the permissions already embedded
in the JWT at login time (see identity module) - no extra DB round-trip per
request, matching the design decision in
docs/architecture/04-appointment-engine-and-identity.md section 4.2."""
from __future__ import annotations

from fastapi import Depends, Request

from core.application.exceptions import ForbiddenException
from modules.identity.presentation.dependencies import get_current_claims


def require_permission(permission_code: str):
    async def _checker(claims: dict = Depends(get_current_claims)) -> dict:
        permissions = claims.get("permissions") or []
        if permission_code not in permissions:
            raise ForbiddenException(
                f"Missing required permission: {permission_code}",
                details={"required_permission": permission_code},
            )
        return claims

    return _checker
