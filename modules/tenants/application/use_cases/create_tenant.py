from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.result import Error, Result
from modules.tenants.application.dtos import CreateTenantRequest, TenantResponse
from modules.tenants.domain.entities import Tenant
from modules.tenants.infrastructure.models import TenantModel
from modules.tenants.infrastructure.repositories import TenantRepository


class CreateTenant:
    """Public self-service tenant sign-up: creates the Tenant row. Does NOT
    touch TenantContext (there is no tenant yet) - this is the one Use Case
    in the whole system allowed to write without a tenant scope."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = TenantRepository(session)

    async def execute(self, request: CreateTenantRequest) -> Result[TenantResponse]:
        existing = await self._repo.get_by_slug(request.slug)
        if existing is not None:
            return Result.failure(Error(code="CONFLICT", message=f"Slug '{request.slug}' is already taken."))

        try:
            tenant = Tenant(name=request.name, slug=request.slug)
        except ValueError as exc:
            return Result.failure(Error(code="VALIDATION_ERROR", message=str(exc)))

        model = TenantModel(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            status=tenant.status.value,
            created_at=tenant.created_at,
        )
        self._session.add(model)
        await self._session.flush()

        return Result.success(
            TenantResponse(id=model.id, name=model.name, slug=model.slug, status=model.status)
        )
