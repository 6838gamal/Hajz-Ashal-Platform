---
name: Nullable column in a composite primary key
description: PostgreSQL cannot have NULL in any column that is part of a PRIMARY KEY, even if the app logic wants that column optional.
---

A many-to-many/link table where one of the natural-key columns is legitimately optional (e.g. `user_roles(user_id, role_id, branch_id)` where a role can be tenant-wide or scoped to one branch) cannot use that natural key as a composite `PRIMARY KEY`, because Postgres implicitly enforces `NOT NULL` on every PK column.

**Why:** Inserting a row with the optional column left `NULL` fails with `null value in column "..." violates not-null constraint`, even though the ORM model declared it `nullable=True` — the PK constraint overrides that.

**How to apply:** Give the table a surrogate primary key (e.g. `id UUID`) and enforce the natural key via a `UNIQUE` constraint instead (`UniqueConstraint(col_a, col_b, nullable_col)`). Unique constraints in Postgres treat multiple `NULL`s as distinct, so this preserves the "optional scoping" semantics that a composite PK cannot.
