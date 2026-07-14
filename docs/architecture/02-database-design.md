# 2. تصميم قاعدة البيانات

## 2.1 مبادئ عامة لكل الجداول
- `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- `tenant_id UUID NOT NULL REFERENCES tenants(id)` — في كل جدول متعلق بمستأجر (Row-Level Isolation)، مع Composite Index `(tenant_id, id)` وسياسة تطبيقية تفرض تمرير `tenant_id` في كل Query (عبر Base Repository + Postgres Row Level Security كخط دفاع ثانٍ).
- حقول التدقيق: `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ`, `deleted_at TIMESTAMPTZ` (Soft Delete), `created_by UUID`, `updated_by UUID`, `deleted_by UUID`, `version INTEGER NOT NULL DEFAULT 1` (Optimistic Locking).
- Soft Delete: لا حذف فعلي؛ فهارس جزئية `WHERE deleted_at IS NULL` لتسريع الاستعلامات الحيّة.
- Naming: snake_case، جمع (plural) لأسماء الجداول.

## 2.2 الجداول الأساسية (Platform)

**tenants**(id, name, slug UNIQUE, status[active|suspended|trial], created_at...)

**branches**(id, tenant_id FK, name, address, timezone, status, ...) — Index(tenant_id)

**users**(id, tenant_id FK NULLABLE للمستخدمين عبر-المستأجرين إن وُجد, email UNIQUE per tenant, hashed_password, full_name, status, last_login_at, ...) — Unique(tenant_id, email)

**roles**(id, tenant_id FK NULLABLE لأدوار نظام عامة, name, is_system_role, ...) — Unique(tenant_id, name)

**permissions**(id, code UNIQUE, module, description) — جدول عام غير مرتبط بـ tenant (Catalog ثابت يُدار بالكود/Migrations)

**role_permissions**(role_id FK, permission_id FK, PRIMARY KEY(role_id, permission_id))

**user_roles**(user_id FK, role_id FK, branch_id FK NULLABLE لتقييد الدور بفرع معيّن, PRIMARY KEY(user_id, role_id, branch_id))

**refresh_tokens**(id, user_id FK, token_hash, expires_at, revoked_at, ...) — Index(user_id)

**subscription_plans**(id, code UNIQUE, name, price, billing_cycle[monthly|yearly], limits JSONB, features JSONB) — Catalog عام

**subscriptions**(id, tenant_id FK UNIQUE, plan_id FK, status[trial|active|past_due|canceled], trial_ends_at, current_period_start, current_period_end, ...)

**usage_counters**(id, tenant_id FK, metric_key, period_start, period_end, value) — Unique(tenant_id, metric_key, period_start)

**invoices**(id, tenant_id FK, subscription_id FK NULLABLE, amount, currency, status[draft|open|paid|void], due_at, ...)

**payments**(id, tenant_id FK, invoice_id FK NULLABLE, amount, method, status, provider_reference, paid_at, ...)

**notifications**(id, tenant_id FK, user_id FK NULLABLE, channel[email|sms|inapp|webhook], template_key, payload JSONB, status[pending|sent|failed], scheduled_at, sent_at, ...) — Index(tenant_id, status, scheduled_at) — يُستخدم أيضاً كـ Outbox Table لمعالجة داخلية بدون طابور خارجي.

**audit_logs**(id, tenant_id FK NULLABLE, actor_user_id, action, entity_type, entity_id, before JSONB, after JSONB, ip_address, created_at) — Index(tenant_id, entity_type, entity_id)

**files**(id, tenant_id FK, owner_type, owner_id, storage_path, mime_type, size_bytes, ...) — Index(tenant_id, owner_type, owner_id)

**settings**(id, tenant_id FK, branch_id FK NULLABLE, key, value JSONB) — Unique(tenant_id, branch_id, key)

## 2.3 جداول قطاع العيادات

**clinics**(id, tenant_id FK, branch_id FK, name, specialty, ...)

**doctors**(id, tenant_id FK, clinic_id FK, user_id FK NULLABLE (إن كان الطبيب مستخدم نظام), full_name, specialty, ...)

**patients**(id, tenant_id FK, full_name, phone, email, date_of_birth, medical_notes, ...) — Index(tenant_id, phone)

**medical_services**(id, tenant_id FK, clinic_id FK, name, duration_minutes, price, ...)

**rooms**(id, tenant_id FK, branch_id FK, name, capacity, ...)

**working_hours**(id, tenant_id FK, doctor_id FK NULLABLE (أو room_id/clinic_id), day_of_week, start_time, end_time) — يدعم Doctor-level أو Clinic-level

**doctor_time_off**(id, tenant_id FK, doctor_id FK, start_at, end_at, reason[vacation|blocked|break]) — لتغطية Vacation/Break/Blocked Time

**appointments**(id, tenant_id FK, branch_id FK, clinic_id FK, doctor_id FK, patient_id FK, room_id FK NULLABLE, service_id FK, start_at, end_at, status[requested|confirmed|checked_in|completed|canceled|no_show], is_recurring, recurrence_rule JSONB NULLABLE, waiting_list_position INTEGER NULLABLE, canceled_reason, ...)
  - **Exclusion Constraint** (PostgreSQL `EXCLUDE USING gist`) على `(doctor_id, tsrange(start_at, end_at))` مع شرط `status NOT IN ('canceled')` لمنع التعارض على مستوى قاعدة البيانات نفسها، بالإضافة إلى فحص تطبيقي في Domain Service.
  - Index(tenant_id, doctor_id, start_at), Index(tenant_id, patient_id)

**appointment_status_history**(id, appointment_id FK, from_status, to_status, changed_by, changed_at, note) — لسجل تتبّع الحالة (Workflow Audit)

**waiting_list_entries**(id, tenant_id FK, clinic_id FK, doctor_id FK NULLABLE, patient_id FK, desired_date_range, status[waiting|offered|expired|converted], created_at)

## 2.4 الفهارس والقيود (تلخيص)
- Foreign Keys: `ON DELETE RESTRICT` كقاعدة عامة (لا حذف يكسر التاريخ)؛ Soft Delete يغطي معظم حالات "الحذف".
- Unique Constraints: مذكورة أعلاه لكل جدول له مفتاح طبيعي (email, slug, plan code...).
- Composite Indexes لكل استعلام متوقع بكثرة: `(tenant_id, *)` في جميع الجداول متعددة المستأجرين.
- Partial Indexes: `WHERE deleted_at IS NULL` على الجداول الكبيرة (appointments, patients, users).
- Row Level Security (RLS) في PostgreSQL مفعّلة على كل جدول يحمل `tenant_id`، بحيث تُمرَّر `current_setting('app.tenant_id')` من الـ Session قبل كل Query — خط دفاع ثانٍ إضافي على مستوى Infrastructure Layer، مستقل عن منطق التطبيق.

## 2.5 Migrations
- Alembic لكل Module بمجلد Migrations خاص به (`modules/<name>/infrastructure/database/migrations/`)، مجمّعة عبر Migration Registry واحد في وقت التشغيل — بحيث كل Module يضيف Migrations خاصة به دون تعديل ملف مركزي.
