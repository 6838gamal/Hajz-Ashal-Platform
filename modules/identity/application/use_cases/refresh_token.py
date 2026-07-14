from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.result import Error, Result
from core.infrastructure.security import create_access_token
from modules.access_control.application.public_api import get_roles_and_permissions_for_user
from modules.identity.application.dtos import RefreshTokenRequest, TokenPairResponse
from modules.identity.infrastructure.models import RefreshTokenModel
from modules.identity.infrastructure.repositories import RefreshTokenRepository, UserRepository


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class RefreshAccessToken:
    """Rotation: the presented refresh token is revoked immediately and a
    brand new pair is issued, so a stolen-and-reused token is detectable
    (its hash will already be revoked)."""

    def __init__(self, session: AsyncSession, *, jwt_secret: str, access_ttl_minutes: int, refresh_ttl_days: int):
        self._session = session
        self._refresh_repo = RefreshTokenRepository(session)
        self._user_repo = UserRepository(session)
        self._jwt_secret = jwt_secret
        self._access_ttl_minutes = access_ttl_minutes
        self._refresh_ttl_days = refresh_ttl_days

    async def execute(self, request: RefreshTokenRequest) -> Result[TokenPairResponse]:
        try:
            token_id_str, raw_secret = request.refresh_token.split(".", 1)
            token_id = uuid.UUID(token_id_str)
        except (ValueError, AttributeError):
            return Result.failure(Error(code="UNAUTHORIZED", message="Malformed refresh token."))

        stored = await self._refresh_repo.get_by_id(token_id)
        if stored is None or stored.revoked_at is not None:
            return Result.failure(Error(code="UNAUTHORIZED", message="Refresh token is invalid or already used."))
        if stored.expires_at < datetime.now(timezone.utc):
            return Result.failure(Error(code="UNAUTHORIZED", message="Refresh token expired."))
        if stored.token_hash != _hash_token(raw_secret):
            return Result.failure(Error(code="UNAUTHORIZED", message="Refresh token is invalid."))

        await self._refresh_repo.revoke(stored)

        # Look up the user without relying on TenantContext (not set on refresh calls).
        from modules.identity.infrastructure.models import UserModel

        user = await self._session.get(UserModel, stored.user_id)
        if user is None:
            return Result.failure(Error(code="UNAUTHORIZED", message="User no longer exists."))

        roles, permissions = await get_roles_and_permissions_for_user(self._session, user.id)

        access_token = create_access_token(
            secret_key=self._jwt_secret,
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=roles,
            permissions=permissions,
            ttl_minutes=self._access_ttl_minutes,
        )

        raw_refresh_token = uuid.uuid4().hex + uuid.uuid4().hex
        new_refresh = RefreshTokenModel(
            user_id=user.id,
            token_hash=_hash_token(raw_refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=self._refresh_ttl_days),
            created_at=datetime.now(timezone.utc),
        )
        await self._refresh_repo.add(new_refresh)

        return Result.success(TokenPairResponse(access_token=access_token, refresh_token=f"{new_refresh.id}.{raw_refresh_token}"))
