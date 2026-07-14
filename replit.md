# منصة SaaS لإدارة وحجز المواعيد (Clinics-first, Multi-Sector Ready)

## نظرة عامة
مشروع جديد (المستودع المستورد كان فارغاً بالكامل). المرحلة الحالية: **تصميم فقط، بلا كود** — بحسب طلب المستخدم الصريح ("لا تبدأ بالكود إلا بعد انتهاء التصميم").

الهدف النهائي: منصة SaaS متعددة المستأجرين (Multi-Tenant) لإدارة وحجز المواعيد، تبدأ بقطاع العيادات الطبية، ومبنية كـ **Modular Monolith** (Python + FastAPI + PostgreSQL + Docker فقط) بحيث يمكن إضافة قطاعات جديدة (مطاعم، صالونات، ورش...) لاحقاً كموديولات مستقلة دون تعديل الأساس (Core).

## وثائق التصميم
كل تصميم النظام (Domains، Modules، قاعدة البيانات، الطبقات، APIs، محرك المواعيد، Identity، Dashboard/Reporting، الاشتراكات، هيكل المجلدات، Docker/Deployment) موجود في:
- `docs/architecture/README.md` — فهرس رئيسي
- `docs/architecture/01-analysis-and-domains.md`
- `docs/architecture/02-database-design.md`
- `docs/architecture/03-layers-and-api-design.md`
- `docs/architecture/04-appointment-engine-and-identity.md`
- `docs/architecture/05-dashboard-reporting-subscription.md`
- `docs/architecture/06-folder-structure-and-deployment.md`

## القيود التقنية (ثابتة، لا تُخرق بدون موافقة المستخدم)
Python, FastAPI, PostgreSQL, Docker فقط. ممنوع: Redis, Celery, RabbitMQ, Kafka, MongoDB, Firebase, Supabase, Elasticsearch, GraphQL, gRPC, Microservices. المشروع Monolith Modular وليس Microservices.

## User preferences
- المستخدم يفضّل التواصل بالعربية.
- طلب صراحة: لا كتابة كود قبل اكتمال ومراجعة التصميم الكامل (Architecture & Design) أولاً.
- المشروع يجب أن يبقى Modular Monolith قابل للتوسع بإضافة قطاعات/ميزات كموديولات مستقلة دون تعديل Core.
- لا تستبدل أي رابط أو خدمة خارجية بمكافئ محلي (مثال: لا تستبدل قاعدة البيانات الخارجية بقاعدة Replit المدمجة). دع كل الإعدادات الخارجية كما هي بدون تعديل إلا بطلب صريح.

## حالة البناء الحالية
تم بناء الأساس (Foundation): Core + Tenants + Identity + RBAC scaffolding (access_control)، متوافق مع التصميم في `docs/architecture/`.

**كيفية التشغيل:**
- Workflow: `Start application` يشغّل `uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload`.
- التوثيق التفاعلي: `/docs` (Swagger)، `/health` و `/health/ready` لفحوصات الصحة.
- قاعدة البيانات: **Render Postgres خارجية** (وليست قاعدة Replit المدمجة) — الاتصال عبر السر `EXTERNAL_DATABASE_URL` (له الأولوية دائماً على `DATABASE_URL`)، عبر SQLAlchemy async + asyncpg. هذا قرار صريح من المستخدم؛ لا تُرجع الاتصال إلى قاعدة Replit المدمجة دون طلب واضح.
- Migrations: `alembic upgrade head` (بعد `export PYTHONPATH="$PWD"`). لإنشاء migration جديدة بعد تعديل أي ORM model: `alembic revision --autogenerate -m "..."`.
- تعبئة كتالوج الصلاحيات: `python scripts/seed_permissions.py`.
- `JWT_SECRET`: يُقرأ من متغير البيئة `JWT_SECRET`، وإن لم يوجد يُستخدم `SESSION_SECRET` كبديل احتياطي فقط في التطوير.

**ما تم تنفيذه فعلياً:**
- `POST /api/v1/tenants` — تسجيل مستأجر جديد (Self-service sign-up).
- `POST /api/v1/tenants/branches` — إنشاء فرع (محمي بصلاحية `tenants.branches.create`).
- `POST /api/v1/auth/register` — تسجيل مستخدم داخل مستأجر معيّن.
- `POST /api/v1/auth/login` — تسجيل دخول، يُعيد Access + Refresh Token (الصلاحيات/الأدوار مضمّنة في الـ JWT).
- `POST /api/v1/auth/refresh` — تدوير Refresh Token (Rotation)، الرمز القديم يُبطَل فوراً.
- RBAC: `roles/permissions/role_permissions/user_roles` + `require_permission(...)` Dependency تفحص الصلاحيات المضمّنة في JWT.
- Tenant Isolation مطبّق تطبيقياً عبر `TenantContext` + `BaseRepository` (يستحيل الاستعلام بدون Tenant scope). ملاحظة: Row-Level Security على مستوى PostgreSQL (خط الدفاع الثاني المذكور في التصميم) لم يُفعَّل بعد.
- تم التحقق يدويًا: إنشاء Tenant → تسجيل مستخدم → تسجيل دخول → فشل بدون صلاحية (403) → نجاح بعد منح الصلاحية (201) → رفض إعادة استخدام Refresh Token القديم (401).

**الخطوة التالية:** باقي الموديولات حسب الترتيب في `01-analysis-and-domains.md` (clinics/doctors/patients/medical_services/rooms، ثم appointments كمحرك المواعيد، ثم billing/subscriptions/dashboard/reporting).
