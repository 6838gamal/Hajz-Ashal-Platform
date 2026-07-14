from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from core.application.exceptions import ConflictException, ForbiddenException, ValidationException
from core.presentation.responses import ApiResponse
from modules.access_control.presentation.dependencies import require_permission
from modules.identity.presentation.dependencies import get_current_claims
from modules.tenants.application.dtos import CreateBranchRequest, CreateTenantRequest
from modules.tenants.application.use_cases.create_branch import CreateBranch
from modules.tenants.application.use_cases.create_tenant import CreateTenant
from modules.tenants.presentation.schemas import (
    BranchSchema,
    CreateBranchSchema,
    CreateTenantSchema,
    TenantSchema,
)

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.post("", response_model=ApiResponse[TenantSchema], status_code=201)
async def create_tenant(payload: CreateTenantSchema, session: AsyncSession = Depends(get_session)):
    """Public sign-up endpoint - no auth required, this is how a new
    customer onboards onto the platform."""
    use_case = CreateTenant(session)
    result = await use_case.execute(CreateTenantRequest(name=payload.name, slug=payload.slug))
    if result.is_failure:
        if result.error.code == "CONFLICT":
            raise ConflictException(result.error.message)
        raise ValidationException(result.error.message)
    tenant = result.value
    return ApiResponse.ok(TenantSchema(id=tenant.id, name=tenant.name, slug=tenant.slug, status=tenant.status))


@router.post("/branches", response_model=ApiResponse[BranchSchema], status_code=201)
async def create_branch(
    payload: CreateBranchSchema,
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(require_permission("tenants.branches.create")),
):
    tenant_id = uuid.UUID(claims["tenant_id"])
    use_case = CreateBranch(session)
    result = await use_case.execute(
        CreateBranchRequest(tenant_id=tenant_id, name=payload.name, address=payload.address, timezone=payload.timezone)
    )
    if result.is_failure:
        if result.error.code == "FORBIDDEN":
            raise ForbiddenException(result.error.message)
        raise ValidationException(result.error.message)
    branch = result.value
    return ApiResponse.ok(
        BranchSchema(id=branch.id, tenant_id=branch.tenant_id, name=branch.name, address=branch.address, timezone=branch.timezone)
    )
