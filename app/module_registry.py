"""Every enabled Module registers itself here. Adding a new sector/feature
module later means adding one import + one line, per
docs/architecture/01-analysis-and-domains.md (self-registration)."""
from __future__ import annotations

from fastapi import FastAPI

from modules.access_control.module import register as register_access_control
from modules.identity.module import register as register_identity
from modules.tenants.module import register as register_tenants

# NOTE: platform_admin is intentionally NOT registered here. It runs as its
# own standalone FastAPI app (see admin/main.py) so it can be deployed
# to a separate server, independent from this tenant-facing app.
_REGISTERED_MODULES = [
    register_access_control,  # no dependencies
    register_tenants,  # no dependencies
    register_identity,  # depends on tenants + access_control
]


def register_all_modules(app: FastAPI) -> None:
    for register in _REGISTERED_MODULES:
        register(app)
