from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.result import Error, Result
from core.infrastructure.security import create_access_token, verify_password
from modules.access_control.application.public_api import get_roles_and_permissions_for_user
from modules.identity.application.dtos import LoginRequest, TokenPairResponse
from modules.identity.infrastructure.models import RefreshTokenModel
from modules.identity.infrastructure.repositories import RefreshTokenRepository, UserRepository


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class Login:
    def __init__(self, session: AsyncSession, *, jwt_secret: str, access_ttl_minutes: int, refresh_ttl_days: int):
        self._session = session
        self._user_repo = UserRepository(session)
        self._refresh_repo = RefreshTokenRepository(session)
        self._jwt_secret = jwt_secret
        self._access_ttl_minutes = access_ttl_minutes
        self._refresh_ttl_days = refresh_ttl_days

    async def execute(self, request: LoginRequest) -> Result[TokenPairResponse]:
        user = await self._user_repo.get_by_email(request.tenant_id, request.email)
        if user is None or not verify_password(request.password, user.hashed_password):
            return Result.failure(Error(code="UNAUTHORIZED", message="Invalid email or password."))
        if user.status != "active":
            return Result.failure(Error(code="FORBIDDEN", message="This account is disabled."))

        roles, permissions = await get_roles_and_permissions_for_user(self._session, user.id)

        access_token = create_access_token(
            secret_key=self._jwt_secret,
            user_id=user.id,
            tenant_id=user.tenant_id,
            roles=roles,
            permissions=permissions,
            ttl_minutes=self._access_ttl_minutes,
        )

        import uuid as _uuid

        raw_refresh_token = _uuid.uuid4().hex + _uuid.uuid4().hex
        refresh_model = RefreshTokenModel(
            user_id=user.id,
            token_hash=_hash_token(raw_refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=self._refresh_ttl_days),
            created_at=datetime.now(timezone.utc),
        )
        await self._refresh_repo.add(refresh_model)

        user.last_login_at = datetime.now(timezone.utc)
        await self._session.flush()

        return Result.success(TokenPairResponse(access_token=access_token, refresh_token=f"{refresh_model.id}.{raw_refresh_token}"))
