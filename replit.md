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

## الخطوة التالية
بانتظار مراجعة المستخدم لوثائق `docs/architecture/`. بعد الموافقة (أو طلب تعديلات)، تبدأ مرحلة البناء التدريجي: Core + Identity + Tenants أولاً، ثم باقي الموديولات حسب الترتيب المذكور في `01-analysis-and-domains.md`.
