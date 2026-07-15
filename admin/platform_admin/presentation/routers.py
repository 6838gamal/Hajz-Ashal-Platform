from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.settings import get_settings
from core.application.exceptions import ConflictException, NotFoundException, UnauthorizedException
from core.presentation.responses import ApiMeta, ApiResponse
from modules.access_control.application import public_api as access_control_api
from modules.identity.application import public_api as identity_api
from admin.platform_admin.application.dtos import PlatformLoginRequest
from admin.platform_admin.application.use_cases.login import PlatformAdminLogin
from admin.platform_admin.infrastructure.repositories import PlatformAdminRepository
from admin.platform_admin.presentation.dependencies import get_current_platform_admin
from admin.platform_admin.presentation.schemas import (
    AssignRoleSchema,
    BranchAdminSchema,
    BranchCreateSchema,
    BranchUpdateSchema,
    PermissionSchema,
    PlatformAdminMeSchema,
    PlatformLoginSchema,
    PlatformTokenSchema,
    RoleAdminSchema,
    RoleCreateSchema,
    RoleUpdateSchema,
    TenantAdminSchema,
    TenantUpdateSchema,
    UserAdminSchema,
    UserCreateSchema,
    UserUpdateSchema,
)
from modules.tenants.application import public_api as tenants_api

router = APIRouter(prefix="/api/v1/platform-admin", tags=["platform-admin"])


def _pagination_meta(page: int, page_size: int, total: int) -> ApiMeta:
    return ApiMeta(page=page, page_size=page_size, total=total)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@router.post("/auth/login", response_model=ApiResponse[PlatformTokenSchema])
async def login(payload: PlatformLoginSchema, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    use_case = PlatformAdminLogin(
        session,
        jwt_secret=settings.jwt_secret,
        access_ttl_minutes=settings.platform_admin_token_ttl_minutes,
    )
    result = await use_case.execute(PlatformLoginRequest(email=payload.email, password=payload.password))
    if result.is_failure:
        raise UnauthorizedException(result.error.message)
    tokens = result.value
    return ApiResponse.ok(
        PlatformTokenSchema(access_token=tokens.access_token, full_name=tokens.full_name, email=tokens.email)
    )


@router.get("/me", response_model=ApiResponse[PlatformAdminMeSchema])
async def me(
    session: AsyncSession = Depends(get_session),
    claims: dict = Depends(get_current_platform_admin),
):
    repo = PlatformAdminRepository(session)
    admin = await repo.get_by_id(claims["admin_id"])
    if admin is None:
        raise NotFoundException("Admin account not found.")
    return ApiResponse.ok(
        PlatformAdminMeSchema(id=admin.id, email=admin.email, full_name=admin.full_name, status=admin.status)
    )


# ---------------------------------------------------------------------------
# Tenants
# ---------------------------------------------------------------------------


@router.get("/tenants", response_model=ApiResponse[list[TenantAdminSchema]])
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = None,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    rows, total = await tenants_api.list_tenants(session, page=page, page_size=page_size, search=search)
    data = [TenantAdminSchema(id=t.id, name=t.name, slug=t.slug, status=t.status) for t in rows]
    return ApiResponse.ok(data, meta=_pagination_meta(page, page_size, total))


@router.get("/tenants/{tenant_id}", response_model=ApiResponse[TenantAdminSchema])
async def get_tenant(
    tenant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    tenant = await tenants_api.get_tenant(session, tenant_id)
    if tenant is None or tenant.deleted_at is not None:
        raise NotFoundException("Tenant not found.")
    return ApiResponse.ok(TenantAdminSchema(id=tenant.id, name=tenant.name, slug=tenant.slug, status=tenant.status))


@router.patch("/tenants/{tenant_id}", response_model=ApiResponse[TenantAdminSchema])
async def update_tenant(
    tenant_id: uuid.UUID,
    payload: TenantUpdateSchema,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    tenant = await tenants_api.update_tenant(session, tenant_id, name=payload.name, status=payload.status)
    if tenant is None:
        raise NotFoundException("Tenant not found.")
    return ApiResponse.ok(TenantAdminSchema(id=tenant.id, name=tenant.name, slug=tenant.slug, status=tenant.status))


@router.delete("/tenants/{tenant_id}", response_model=ApiResponse[dict])
async def delete_tenant(
    tenant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    ok = await tenants_api.delete_tenant(session, tenant_id)
    if not ok:
        raise NotFoundException("Tenant not found.")
    return ApiResponse.ok({"deleted": True})


# ---------------------------------------------------------------------------
# Branches
# ---------------------------------------------------------------------------


@router.get("/tenants/{tenant_id}/branches", response_model=ApiResponse[list[BranchAdminSchema]])
async def list_branches(
    tenant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    tenant = await tenants_api.get_tenant(session, tenant_id)
    if tenant is None or tenant.deleted_at is not None:
        raise NotFoundException("Tenant not found.")
    rows = await tenants_api.list_branches(session, tenant_id)
    data = [
        BranchAdminSchema(id=b.id, tenant_id=b.tenant_id, name=b.name, address=b.address, timezone=b.timezone)
        for b in rows
    ]
    return ApiResponse.ok(data)


@router.post("/tenants/{tenant_id}/branches", response_model=ApiResponse[BranchAdminSchema], status_code=201)
async def create_branch(
    tenant_id: uuid.UUID,
    payload: BranchCreateSchema,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    branch = await tenants_api.create_branch_for_tenant(
        session, tenant_id, name=payload.name, address=payload.address, timezone_=payload.timezone
    )
    if branch is None:
        raise NotFoundException("Tenant not found.")
    return ApiResponse.ok(
        BranchAdminSchema(id=branch.id, tenant_id=branch.tenant_id, name=branch.name, address=branch.address, timezone=branch.timezone)
    )


@router.patch("/branches/{branch_id}", response_model=ApiResponse[BranchAdminSchema])
async def update_branch(
    branch_id: uuid.UUID,
    payload: BranchUpdateSchema,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    branch = await tenants_api.update_branch(
        session, branch_id, name=payload.name, address=payload.address, timezone_=payload.timezone
    )
    if branch is None:
        raise NotFoundException("Branch not found.")
    return ApiResponse.ok(
        BranchAdminSchema(id=branch.id, tenant_id=branch.tenant_id, name=branch.name, address=branch.address, timezone=branch.timezone)
    )


@router.delete("/branches/{branch_id}", response_model=ApiResponse[dict])
async def delete_branch(
    branch_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    ok = await tenants_api.delete_branch(session, branch_id)
    if not ok:
        raise NotFoundException("Branch not found.")
    return ApiResponse.ok({"deleted": True})


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@router.get("/users", response_model=ApiResponse[list[UserAdminSchema]])
async def list_users(
    tenant_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = None,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    rows, total = await identity_api.list_users(session, tenant_id=tenant_id, page=page, page_size=page_size, search=search)
    data = [UserAdminSchema(id=u.id, tenant_id=u.tenant_id, email=u.email, full_name=u.full_name, status=u.status) for u in rows]
    return ApiResponse.ok(data, meta=_pagination_meta(page, page_size, total))


@router.post("/users", response_model=ApiResponse[UserAdminSchema], status_code=201)
async def create_user(
    payload: UserCreateSchema,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    user, err = await identity_api.create_user_admin(
        session, tenant_id=payload.tenant_id, email=payload.email, password=payload.password, full_name=payload.full_name
    )
    if err == "TENANT_NOT_FOUND":
        raise NotFoundException("Tenant not found.")
    if err == "EMAIL_TAKEN":
        raise ConflictException("Email already registered for this tenant.")
    return ApiResponse.ok(UserAdminSchema(id=user.id, tenant_id=user.tenant_id, email=user.email, full_name=user.full_name, status=user.status))


@router.patch("/users/{user_id}", response_model=ApiResponse[UserAdminSchema])
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateSchema,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    user = await identity_api.update_user_admin(session, user_id, full_name=payload.full_name, status=payload.status, password=payload.password)
    if user is None:
        raise NotFoundException("User not found.")
    return ApiResponse.ok(UserAdminSchema(id=user.id, tenant_id=user.tenant_id, email=user.email, full_name=user.full_name, status=user.status))


@router.delete("/users/{user_id}", response_model=ApiResponse[dict])
async def delete_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    ok = await identity_api.delete_user_admin(session, user_id)
    if not ok:
        raise NotFoundException("User not found.")
    return ApiResponse.ok({"deleted": True})


# ---------------------------------------------------------------------------
# Roles & permissions
# ---------------------------------------------------------------------------


@router.get("/permissions", response_model=ApiResponse[list[PermissionSchema]])
async def list_permissions(
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    rows = await access_control_api.list_permissions(session)
    return ApiResponse.ok([PermissionSchema(id=p.id, code=p.code, module=p.module, description=p.description) for p in rows])


@router.get("/roles", response_model=ApiResponse[list[RoleAdminSchema]])
async def list_roles(
    tenant_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    rows = await access_control_api.list_roles(session, tenant_id=tenant_id)
    data = []
    for r in rows:
        codes = await access_control_api.get_role_permission_codes(session, r.id)
        data.append(RoleAdminSchema(id=r.id, tenant_id=r.tenant_id, name=r.name, is_system_role=r.is_system_role, permission_codes=codes))
    return ApiResponse.ok(data)


@router.post("/roles", response_model=ApiResponse[RoleAdminSchema], status_code=201)
async def create_role(
    payload: RoleCreateSchema,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    if payload.tenant_id is not None and not await tenants_api.tenant_exists(session, payload.tenant_id):
        raise NotFoundException("Tenant not found.")
    role = await access_control_api.create_role(session, tenant_id=payload.tenant_id, name=payload.name, permission_codes=payload.permission_codes)
    codes = await access_control_api.get_role_permission_codes(session, role.id)
    return ApiResponse.ok(RoleAdminSchema(id=role.id, tenant_id=role.tenant_id, name=role.name, is_system_role=role.is_system_role, permission_codes=codes))


@router.patch("/roles/{role_id}", response_model=ApiResponse[RoleAdminSchema])
async def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdateSchema,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    role = await access_control_api.update_role(session, role_id, name=payload.name, permission_codes=payload.permission_codes)
    if role is None:
        raise NotFoundException("Role not found.")
    codes = await access_control_api.get_role_permission_codes(session, role.id)
    return ApiResponse.ok(RoleAdminSchema(id=role.id, tenant_id=role.tenant_id, name=role.name, is_system_role=role.is_system_role, permission_codes=codes))


@router.delete("/roles/{role_id}", response_model=ApiResponse[dict])
async def delete_role(
    role_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    ok = await access_control_api.delete_role(session, role_id)
    if not ok:
        raise NotFoundException("Role not found.")
    return ApiResponse.ok({"deleted": True})


@router.get("/users/{user_id}/roles", response_model=ApiResponse[list[RoleAdminSchema]])
async def list_user_roles(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    assignments = await access_control_api.list_user_role_assignments(session, user_id)
    data = []
    for assignment, _role_name in assignments:
        role = await access_control_api.get_role(session, assignment.role_id)
        if role is None:
            continue
        codes = await access_control_api.get_role_permission_codes(session, assignment.role_id)
        data.append(RoleAdminSchema(id=role.id, tenant_id=role.tenant_id, name=role.name, is_system_role=role.is_system_role, permission_codes=codes))
    return ApiResponse.ok(data)


@router.post("/users/{user_id}/roles", response_model=ApiResponse[dict], status_code=201)
async def assign_role(
    user_id: uuid.UUID,
    payload: AssignRoleSchema,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    role = await access_control_api.get_role(session, payload.role_id)
    if role is None:
        raise NotFoundException("Role not found.")
    await access_control_api.assign_role_to_user(session, user_id=user_id, role_id=payload.role_id, branch_id=payload.branch_id)
    return ApiResponse.ok({"assigned": True})


@router.delete("/users/{user_id}/roles/{role_id}", response_model=ApiResponse[dict])
async def remove_role(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    branch_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
    _claims: dict = Depends(get_current_platform_admin),
):
    ok = await access_control_api.remove_role_from_user(session, user_id=user_id, role_id=role_id, branch_id=branch_id)
    if not ok:
        raise NotFoundException("Role assignment not found.")
    return ApiResponse.ok({"removed": True})
