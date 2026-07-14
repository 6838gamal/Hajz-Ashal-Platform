from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.result import Error, Result
from core.infrastructure.tenant_context import TenantContext
from modules.tenants.application.dtos import BranchResponse, CreateBranchRequest
from modules.tenants.domain.entities import Branch
from modules.tenants.infrastructure.models import BranchModel
from modules.tenants.infrastructure.repositories import BranchRepository


class CreateBranch:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._repo = BranchRepository(session)

    async def execute(self, request: CreateBranchRequest) -> Result[BranchResponse]:
        if request.tenant_id != TenantContext.require():
            return Result.failure(Error(code="FORBIDDEN", message="Cannot create a branch for another tenant."))

        try:
            branch = Branch(tenant_id=request.tenant_id, name=request.name, address=request.address, timezone=request.timezone)
        except ValueError as exc:
            return Result.failure(Error(code="VALIDATION_ERROR", message=str(exc)))

        model = BranchModel(
            id=branch.id,
            tenant_id=branch.tenant_id,
            name=branch.name,
            address=branch.address,
            timezone=branch.timezone,
            created_at=branch.created_at,
        )
        await self._repo.add(model)

        return Result.success(
            BranchResponse(id=model.id, tenant_id=model.tenant_id, name=model.name, address=model.address, timezone=model.timezone)
        )
