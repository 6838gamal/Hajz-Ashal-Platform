# 6. هيكل المجلدات + Docker + Configuration + Deployment

## 6.1 هيكل المجلدات الجذري (قابل للتوسع لسنوات)
```
project-root/
  app/
    main.py                    # إنشاء FastAPI app، تسجيل Middlewares، تجميع Routers من كل Module
    container.py                # تجميع DI من كل Module
    module_registry.py           # قائمة الموديولات المفعّلة + ترتيب تحميلها
    settings.py                   # Pydantic Settings (env-based)
  core/                           # كما في وثيقة 3.2
  modules/
    identity/
    access_control/
    tenants/
    subscriptions/
    notifications/
    audit/
    files/
    settings/
    dashboard/
    reporting/
    clinics/
    doctors/
    patients/
    medical_services/
    rooms/
    appointments/
    billing_clinical/
    # مستقبلاً: restaurants/, salons/, loyalty/, crm/ ...
  tests/
    unit/<module>/               # اختبارات Domain/Application (بدون DB حقيقية)
    integration/<module>/         # اختبارات Repositories/DB حقيقية (Test Containers)
    e2e/                           # اختبارات API كاملة
  scripts/                          # سكربتات إدارية (seed data, create tenant...)
  alembic/                           # إعدادات Alembic المركزية (تجمع migrations كل Module)
  docker/
    Dockerfile
    docker-compose.yml
    docker-compose.override.yml (dev)
  docs/
    architecture/                     # هذه الوثائق
  pyproject.toml
  .env.example
  README.md
```

## 6.2 قاعدة التسمية والاستيراد
- ممنوع الاستيراد المتبادل بين `modules/*` مباشرة إلا عبر `modules/<name>/application/public_api.py`.
- `core` بدون أي `import modules...` أبداً — يُفحص بأداة Lint مخصّصة (import-linter) ضمن CI مستقبلاً لفرض القاعدة آلياً.

## 6.3 Configuration
- `Pydantic Settings` (`app/settings.py`) تُحمَّل من متغيرات البيئة فقط (لا قيم Hardcoded):
  - `DATABASE_URL`, `JWT_SECRET`, `JWT_ACCESS_TTL_MINUTES`, `JWT_REFRESH_TTL_DAYS`, `ENVIRONMENT` (dev/staging/prod), `CORS_ORIGINS`, `LOG_LEVEL`.
- كل Module يمكن أن يعرّف `ModuleSettings` خاصة به (مثلاً حدود Appointment Engine الافتراضية) تُدمج في `settings.py` المركزي دون كسر مبدأ العزل.

## 6.4 Docker
**Dockerfile (Multi-stage):**
```
FROM python:3.12-slim AS base
# تثبيت poetry/uv + deps فقط (بدون كود) لطبقة Cache منفصلة
FROM base AS runtime
# نسخ الكود، تشغيل عبر uvicorn/gunicorn+uvicorn workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml (تطوير محلي):**
```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [db]
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: [pgdata:/var/lib/postgresql/data]
volumes:
  pgdata:
```
لا خدمات إضافية (Redis/RabbitMQ...) بحسب القيد التقني.

## 6.5 Deployment
- **بيئة واحدة Monolith قابلة للتوسع رأسياً وأفقياً**: عدة Instances خلف Load Balancer (Stateless — JWT بدون Session خادم، والـ Internal Scheduler يُشغَّل في Instance واحد مُعيَّن فقط عبر Advisory Lock في PostgreSQL لمنع تكرار المهام الدورية عند التوسع الأفقي).
- **Migrations**: تُشغَّل كخطوة منفصلة قبل إقلاع أي Instance جديد (`alembic upgrade head` في Init Container/Job).
- **Health Checks**: `/health` (Liveness) و `/health/ready` (Readiness يتحقق من اتصال DB).
- **بيئات**: dev / staging / production، كل واحدة بمتغيرات بيئة مستقلة و DATABASE_URL مستقل؛ لا مشاركة بيانات بين البيئات.
- على Replit تحديداً: PostgreSQL المدارة من Replit (بدون Docker Compose محلي؛ Docker يبقى للـ CI/تشغيل خارج Replit إن احتاج المستخدم ذلك لاحقاً)، والتشغيل عبر Workflow واحد يُشغّل `uvicorn`.
