# 🏛 القرارات المعمارية والتقنية

> هذا الملف يوثّق القرارات المهمة التي اتُّخذت مع السبب — لا تتغير هذه القرارات دون موافقتك.

---

## قاعدة البيانات

**القرار:** استخدام Render Postgres الخارجية بدلاً من قاعدة Replit المدمجة.
- المتغير: `EXTERNAL_DATABASE_URL` له الأولوية دائماً على `DATABASE_URL`.
- السبب: استقرار البيانات في بيئة الإنتاج وعدم الاعتماد على Replit للتخزين الدائم.

---

## asyncpg و sslmode

**القرار:** حذف `sslmode=` من DATABASE_URL قبل تمريرها لـ asyncpg.
- السبب: asyncpg لا يقبل هذا الـ query param وكان يُسبب خطأ عند الاتصال.
- التطبيق: دالة `_to_asyncpg_url()` في `app/settings.py`.

---

## user_roles Primary Key

**القرار:** استخدام surrogate `id` (UUID) بدلاً من Composite PK يشمل `branch_id`.
- السبب: PostgreSQL يرفض NULL في أعمدة PK، و`branch_id` nullable (الدور قد يكون tenant-wide).
- التطبيق: UniqueConstraint على `(user_id, role_id, branch_id)` بدلاً من جعلها PK.

---

## Tenant Isolation

**القرار:** العزل يتم على مستوى التطبيق (Application-Level) عبر `TenantContext` + `BaseRepository`.
- يستحيل الاستعلام بدون tenant scope في أي Repository.
- Row-Level Security على PostgreSQL (خط دفاع ثانٍ) مخطط له لاحقاً ولم يُفعَّل بعد.

---

## JWT Strategy

**القرار:** Access Token (15 دقيقة) + Refresh Token (30 يوم) مع Rotation.
- الـ Refresh Token القديم يُبطَل فور استخدامه.
- الأدوار والصلاحيات مُضمَّنة في Access Token لتجنب DB queries في كل طلب.
- `JWT_SECRET` يأتي من env var، يعود على `SESSION_SECRET` في التطوير فقط.

---

## Stack المحظورة

**القرار الثابت:** لا Redis، لا Celery، لا Kafka، لا MongoDB، لا Firebase، لا Supabase، لا Elasticsearch، لا GraphQL، لا gRPC، لا Microservices.
- المهام المؤجلة تُدار داخل PostgreSQL عبر جداول Outbox/Jobs + Worker داخلي.

---

## Modular Monolith Rules

**القرار:** لا استيراد مباشر بين تفاصيل الموديولات — التواصل عبر:
1. `public_api.py` (Application-level Ports)
2. Domain Events

الاتجاه المسموح فقط: قطاع ← Platform Modules ← Core.
العكس ممنوع تماماً.
