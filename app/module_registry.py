"""Every enabled Module registers itself here. Adding a new sector/feature
module later means adding one import + one line, per
docs/architecture/01-analysis-and-domains.md (self-registration)."""
from __future__ import annotations

from fastapi import FastAPI

from modules.access_control.module import register as register_access_control
from modules.identity.module import register as register_identity
from modules.platform_admin.module import register as register_platform_admin
from modules.tenants.module import register as register_tenants

_REGISTERED_MODULES = [
    register_access_control,  # no dependencies
    register_tenants,  # no dependencies
    register_identity,  # depends on tenants + access_control
    register_platform_admin,  # depends on tenants + identity + access_control (via their public_api)
]


def register_all_modules(app: FastAPI) -> None:
    for register in _REGISTERED_MODULES:
        register(app)
