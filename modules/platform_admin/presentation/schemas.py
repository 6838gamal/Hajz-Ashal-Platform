from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class PlatformLoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class PlatformTokenSchema(BaseModel):
    access_token: str
    full_name: str
    email: str


class PlatformAdminMeSchema(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    status: str


class TenantAdminSchema(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str


class TenantUpdateSchema(BaseModel):
    name: str | None = None
    status: str | None = Field(default=None, pattern=r"^(trial|active|suspended)$")


class BranchAdminSchema(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    address: str | None
    timezone: str


class BranchCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str | None = None
    timezone: str = "UTC"


class BranchUpdateSchema(BaseModel):
    name: str | None = None
    address: str | None = None
    timezone: str | None = None


class UserAdminSchema(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    full_name: str
    status: str


class UserCreateSchema(BaseModel):
    tenant_id: uuid.UUID
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=200)


class UserUpdateSchema(BaseModel):
    full_name: str | None = None
    status: str | None = Field(default=None, pattern=r"^(active|disabled)$")
    password: str | None = Field(default=None, min_length=8)


class PermissionSchema(BaseModel):
    id: uuid.UUID
    code: str
    module: str
    description: str | None


class RoleAdminSchema(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    name: str
    is_system_role: bool
    permission_codes: list[str] = []


class RoleCreateSchema(BaseModel):
    tenant_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=100)
    permission_codes: list[str] = []


class RoleUpdateSchema(BaseModel):
    name: str | None = None
    permission_codes: list[str] | None = None


class AssignRoleSchema(BaseModel):
    role_id: uuid.UUID
    branch_id: uuid.UUID | None = None
