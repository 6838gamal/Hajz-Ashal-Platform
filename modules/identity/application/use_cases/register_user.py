from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.result import Error, Result
from core.infrastructure.security import hash_password
from modules.identity.application.dtos import RegisterUserRequest, UserResponse
from modules.identity.domain.entities import User
from modules.identity.infrastructure.models import UserModel
from modules.identity.infrastructure.repositories import UserRepository
from modules.tenants.application.public_api import tenant_exists


class RegisterUser:
    """Registration happens *before* a tenant context exists in the request
    (the user isn't authenticated yet), so this Use Case queries directly by
    tenant_id rather than relying on the ambient TenantContext."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = UserRepository(session)

    async def execute(self, request: RegisterUserRequest) -> Result[UserResponse]:
        if not await tenant_exists(self._session, request.tenant_id):
            return Result.failure(Error(code="NOT_FOUND", message="Tenant not found."))

        existing = await self._session.execute(
            select(UserModel).where(
                UserModel.tenant_id == request.tenant_id,
                UserModel.email == request.email,
                UserModel.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is not None:
            return Result.failure(Error(code="CONFLICT", message="Email already registered for this tenant."))

        try:
            user = User(
                tenant_id=request.tenant_id,
                email=request.email,
                hashed_password=hash_password(request.password),
                full_name=request.full_name,
            )
        except ValueError as exc:
            return Result.failure(Error(code="VALIDATION_ERROR", message=str(exc)))

        model = UserModel(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            status=user.status.value,
            created_at=user.created_at,
        )
        self._session.add(model)
        await self._session.flush()

        return Result.success(
            UserResponse(id=model.id, tenant_id=model.tenant_id, email=model.email, full_name=model.full_name, status=model.status)
        )
