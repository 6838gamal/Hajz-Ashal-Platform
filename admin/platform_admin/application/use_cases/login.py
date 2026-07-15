from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.result import Error, Result
from core.infrastructure.security import create_access_token, verify_password
from admin.platform_admin.application.dtos import PlatformLoginRequest, PlatformTokenResponse
from admin.platform_admin.infrastructure.repositories import PlatformAdminRepository


class PlatformAdminLogin:
    def __init__(self, session: AsyncSession, *, jwt_secret: str, access_ttl_minutes: int):
        self._session = session
        self._repo = PlatformAdminRepository(session)
        self._jwt_secret = jwt_secret
        self._access_ttl_minutes = access_ttl_minutes

    async def execute(self, request: PlatformLoginRequest) -> Result[PlatformTokenResponse]:
        admin = await self._repo.get_by_email(request.email)
        if admin is None or not verify_password(request.password, admin.hashed_password):
            return Result.failure(Error(code="UNAUTHORIZED", message="Invalid email or password."))
        if admin.status != "active":
            return Result.failure(Error(code="FORBIDDEN", message="This account is disabled."))

        access_token = create_access_token(
            secret_key=self._jwt_secret,
            user_id=admin.id,
            tenant_id=None,
            roles=["platform_admin"],
            permissions=["*"],
            ttl_minutes=self._access_ttl_minutes,
            scope="platform_admin",
        )
        admin.last_login_at = datetime.now(timezone.utc)
        await self._session.flush()

        return Result.success(
            PlatformTokenResponse(access_token=access_token, full_name=admin.full_name, email=admin.email)
        )
