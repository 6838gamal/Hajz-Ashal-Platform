from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class CreateTenantRequest:
    name: str
    slug: str


@dataclass(frozen=True)
class TenantResponse:
    id: uuid.UUID
    name: str
    slug: str
    status: str


@dataclass(frozen=True)
class CreateBranchRequest:
    tenant_id: uuid.UUID
    name: str
    address: str | None
    timezone: str


@dataclass(frozen=True)
class BranchResponse:
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    address: str | None
    timezone: str
