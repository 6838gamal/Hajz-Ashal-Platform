---
name: Replit Postgres + asyncpg
description: DATABASE_URL from Replit's built-in Postgres includes sslmode=disable, which asyncpg's connect() rejects as an unknown kwarg.
---

Replit's provisioned `DATABASE_URL` looks like `postgresql://user:pass@host/db?sslmode=disable`. SQLAlchemy's `psycopg2` driver accepts `sslmode` fine, but the `asyncpg` driver's `connect()` does not recognize it and raises `TypeError: connect() got an unexpected keyword argument 'sslmode'`.

**Why:** asyncpg has its own SSL config surface (`ssl=` param) and doesn't parse libpq-style query params the way psycopg2 does.

**How to apply:** When building the async SQLAlchemy URL (`postgresql+asyncpg://...`) from `DATABASE_URL`, strip any `sslmode=...` query parameter before handing it to `create_async_engine`. Keep the rest of the query string intact if there is one.
