from __future__ import annotations

from dataclasses import dataclass

from core.domain.base_entity import BaseEntity


@dataclass(kw_only=True)
class PlatformAdmin(BaseEntity):
    """A platform-superadmin account. Deliberately NOT a TenantScopedEntity -
    this is the one identity in the system that sits above every Tenant, per
    the explicit product decision to keep it fully separate from the
    tenant-scoped `identity` module (see admin/decisions.md)."""

    email: str
    hashed_password: str
    full_name: str
    status: str = "active"

    def __post_init__(self) -> None:
        if not self.email.strip():
            raise ValueError("Email must not be empty")
        if not self.full_name.strip():
            raise ValueError("Full name must not be empty")
