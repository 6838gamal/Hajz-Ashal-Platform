from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CreateTenantSchema(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TenantSchema(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str


class CreateBranchSchema(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str | None = None
    timezone: str = "UTC"


class BranchSchema(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    address: str | None
    timezone: str
