---
name: Platform-admin JWT scope convention
description: How the platform-superadmin panel keeps its sessions separate from tenant-user sessions in this booking SaaS.
---

`create_access_token()` takes an optional `scope` param, default `"tenant"`. The
platform-admin login mints tokens with `scope="platform_admin"` instead.

**Why:** the product explicitly wants the platform owner's admin panel
(manages every tenant: tenants/branches/users/roles) to have a login fully
independent from tenant-user accounts — different table, different
dependency, never scoped by `TenantContext`.

**How to apply:** any new auth dependency that trusts cross-tenant claims
must check `claims.get("scope") == "platform_admin"` explicitly (see
`modules/platform_admin/presentation/dependencies.py`) — do not assume a
valid, unexpired JWT is enough. Cross-tenant list/CRUD helpers live in each
module's `public_api.py` (e.g. `tenants.application.public_api.list_tenants`)
and deliberately skip the tenant-scoped base query — this is the one
sanctioned exception to "no query without tenant scope".
