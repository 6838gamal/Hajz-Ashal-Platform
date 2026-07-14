# 3. تصميم الطبقات (Domain/Application/Infrastructure/Presentation) وتصميم API

## 3.1 هيكل كل Module (مطابق للطبقات الأربعة)
```
modules/<module_name>/
  domain/
    entities/            # Entities & Aggregates
    value_objects/        # Value Objects (Email, PhoneNumber, TimeRange, Money...)
    events/               # Domain Events
    services/             # Domain Services (منطق أعمال لا يخص Entity واحد)
    repositories/         # Repository Interfaces (Ports)
    specifications/        # Specification Pattern (قواعد قابلة للتركيب)
    factories/            # Factories لبناء Aggregates معقّدة
    exceptions.py
  application/
    use_cases/            # كل Use Case في ملف مستقل (Command أو Query)
      commands/
      queries/
    dtos/                 # Data Transfer Objects (Pydantic) للدخل/الخرج
    validators/            # قواعد تحقق تطبيقية إضافية (خارج Pydantic)
    interfaces/            # Ports لخدمات خارجية (Notification Sender, File Storage...)
    mappings/              # Entity <-> DTO
    public_api.py          # الواجهة الوحيدة المسموح لباقي الموديولات استدعاؤها
  infrastructure/
    persistence/
      models.py            # SQLAlchemy ORM Models
      repositories.py       # تنفيذ Repository Interfaces
      unit_of_work.py
    migrations/            # Alembic خاص بالموديول
    external/               # تنفيذ Adapters لخدمات خارجية
    di.py                   # تسجيل Providers الخاصة بالموديول في DI Container
  presentation/
    routers.py             # FastAPI APIRouter
    schemas/                # Request/Response Pydantic Models (منفصلة عن DTOs الداخلية)
    dependencies.py          # FastAPI Depends لهذا الموديول
    middlewares.py            # Middlewares خاصة (إن وُجدت)
  module.py                 # نقطة تسجيل الموديول (Routers + DI + Events + Migrations)
```

## 3.2 Core Module (تفاصيل)
```
core/
  domain/
    base_entity.py         # BaseEntity(id, created_at, updated_at, deleted_at, version...)
    base_aggregate_root.py
    result.py               # Result[T] Pattern (Success/Failure بدون Exceptions للتحكم بالتدفق)
    specifications/base_specification.py
  application/
    base_use_case.py         # BaseUseCase[TRequest, TResponse]
    pagination.py             # PageRequest / PageResult[T]
    exceptions.py              # DomainException, NotFoundException, ConflictException...
  infrastructure/
    base_repository.py        # CRUD + Specification-based queries + Tenant scoping تلقائي
    unit_of_work.py             # UnitOfWork عام يُطبَّق بالتخصص لكل Module
    tenant_context.py            # Context محلي (contextvars) لحمل tenant_id الحالي
    security/                     # JWT utils, Password Hashing
  presentation/
    responses.py                 # ApiResponse[T] موحّد {success, data, error, meta}
    error_handlers.py             # Exception -> HTTP mapping موحّد
    middlewares/tenant_middleware.py   # استخراج Tenant من JWT/Header وحقنه في Context
    middlewares/request_id_middleware.py
  constants.py / enums.py
```

## 3.3 مثال تطبيقي كامل: Use Case لحجز موعد (`appointments/application/use_cases/commands/book_appointment.py`)
- **DTO دخل**: `BookAppointmentRequest(tenant_id, branch_id, doctor_id, patient_id, service_id, start_at)`
- **DTO خرج**: `AppointmentResponse(id, status, start_at, end_at, ...)`
- **تسلسل التنفيذ**:
  1. تحميل `WorkingHours` و`DoctorTimeOff` للطبيب (Repository).
  2. Domain Service `AppointmentSchedulingPolicy.validate(...)` يتحقق: داخل ساعات العمل، ليس Break/Vacation، لا تعارض (Specification `NoOverlapSpecification`).
  3. بناء Aggregate `Appointment` عبر `AppointmentFactory` بحالة `requested`.
  4. `UnitOfWork` يحفظ Appointment؛ الاعتماد على DB Exclusion Constraint كخط دفاع أخير ضد Race Conditions.
  5. رفع Domain Event `AppointmentBooked` (يُستهلك لاحقاً من `notifications` و`dashboard` عبر Outbox).
  6. إعادة `Result.success(AppointmentResponse)` أو `Result.failure(ConflictError)`.
- كل خطوة قابلة للاختبار منفردة عبر Fake Repositories (Domain لا يعرف SQLAlchemy).

## 3.4 Value Objects أمثلة
`Email`, `PhoneNumber`, `Money(amount, currency)`, `TimeRange(start, end)` (يتحقق `start < end`), `TenantId`, `Slug` — كل Value Object غير قابل للتغيير (Immutable) ويتحقق من صحته في `__post_init__`.

## 3.5 DTOs
- **Request/Response DTOs** (Application Layer): مستقلة عن HTTP، تُستخدم بين Use Cases.
- **Schemas** (Presentation Layer): Pydantic Models مخصصة لـ FastAPI، تُحوَّل من/إلى DTOs عبر Mapper، لضمان أن تغيّر شكل HTTP API لا يكسر Application Layer والعكس.

## 3.6 Dependency Injection
- Container خفيف مبني فوق `fastapi.Depends` (بدون مكتبة خارجية إضافية): كل Module يعرّف `di.py` يسجّل Providers (Repository Impl -> Interface) في `Container` مركزي بسيط (Dict-based Service Locator + Factory Functions)، يُجمَّع في `app/container.py` عند الإقلاع.
- كل Route يعتمد على Interfaces فقط عبر `Depends(get_use_case(BookAppointment))`، لا على التنفيذ المباشر.

## 3.7 CQRS الداخلي
- **Commands**: تُغيّر الحالة، تُعاد عبر `Result` بدون بيانات كبيرة (Id + Status فقط عادة).
- **Queries**: للقراءة فقط، تسمح بتجاوز Repository الكامل واستخدام SQLAlchemy Core/Read Models مباشرة لتحسين الأداء عند الحاجة (خصوصاً `dashboard` و`reporting`)، دون المرور بـ Aggregates كاملة.
- لا Event Sourcing ولا قاعدة بيانات منفصلة للقراءة — نفس PostgreSQL، فقط فصل منطقي في الكود.

## 3.8 تصميم API (RESTful)
- **Versioning**: `/api/v1/...` بادئة ثابتة، كل Module يسجّل Router تحتها: `/api/v1/appointments`, `/api/v1/doctors`...
- **Response Format موحّد**:
```json
{ "success": true, "data": { ... }, "error": null, "meta": { "request_id": "...", "page": 1, "page_size": 20, "total": 134 } }
```
- **أخطاء موحّدة**:
```json
{ "success": false, "data": null, "error": { "code": "APPOINTMENT_CONFLICT", "message": "...", "details": {} }, "meta": { "request_id": "..." } }
```
- **Pagination**: `?page=1&page_size=20` (Cursor-based اختياري للـ Reporting الثقيل).
- **Filtering/Sorting/Searching**: Query Params موحّدة عبر Spec عام: `?filter[status]=confirmed&sort=-start_at&search=ahmed`.
- **Validation**: عبر Pydantic Schemas + Validators تطبيقية إضافية في Application Layer لقواعد تعتمد على DB (مثل تفرد البريد لكل Tenant).
- **Rate Limiting Ready**: Middleware مُعرَّف بواجهة قابلة للتفعيل (In-memory Token Bucket افتراضيًا داخل الـ Monolith، بدون Redis)، قابل للاستبدال لاحقاً بأي Backend دون تغيير العقد.
- **Auth**: `Authorization: Bearer <JWT>`، الفرع/الـ Tenant يُستخرج من الـ Token أو Header `X-Tenant-Id` عند تسجيل الدخول الأول.

## 3.9 Repository Pattern + Unit of Work
- `BaseRepository[TEntity]` في Core يوفّر: `get_by_id`, `list(spec)`, `add`, `update`, `soft_delete`، وكلها تفرض `tenant_id` تلقائياً من `TenantContext` (يستحيل عمليًا الاستعلام بدون Tenant scope).
- `UnitOfWork` لكل Module يجمع Repositories المتعلقة بمعاملة واحدة (Transaction) ويضمن Commit/Rollback ذري، ويُطلق Domain Events بعد Commit ناجح فقط (Transactional Outbox في جدول `notifications`/`domain_events_outbox`).
