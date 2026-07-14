from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import Enum

from core.domain.base_entity import BaseEntity, TenantScopedEntity

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TenantStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"


@dataclass(kw_only=True)
class Tenant(BaseEntity):
    name: str
    slug: str
    status: TenantStatus = TenantStatus.TRIAL

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Tenant name must not be empty")
        if not _SLUG_RE.match(self.slug):
            raise ValueError("Tenant slug must be lowercase kebab-case (e.g. 'acme-clinics')")


@dataclass(kw_only=True)
class Branch(TenantScopedEntity):
    name: str
    address: str | None = None
    timezone: str = "UTC"
