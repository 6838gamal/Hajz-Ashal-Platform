# 📊 تقرير التقدم — منصة المواعيد

> آخر تحديث: يوليو 2025

---

## ✅ المرحلة الأولى: الأساس (مكتملة)

### Core
- [x] Base Entity, Base Repository, Result Pattern
- [x] Pagination, Common Exceptions
- [x] Middleware (RequestId, TenantContext)
- [x] Unified API Response Envelope
- [x] Security (hash_password, verify_password)

### Tenants Module
- [x] ORM Models: `tenants`, `branches`
- [x] Repository: `get_by_slug`, CRUD
- [x] Use Cases: `CreateTenant`, `CreateBranch`
- [x] API: `POST /api/v1/tenants`, `POST /api/v1/tenants/branches`
- [x] API: `GET /api/v1/tenants/by-slug/{slug}` ← جديد (للواجهة الأمامية)

### Identity Module
- [x] ORM Model: `users`, `refresh_tokens`
- [x] Use Cases: `RegisterUser`, `Login`, `RefreshAccessToken`
- [x] JWT (Access + Refresh) مع Rotation
- [x] API: `POST /api/v1/auth/register`, `/login`, `/refresh`

### Access Control Module (RBAC)
- [x] ORM Models: `roles`, `permissions`, `role_permissions`, `user_roles`
- [x] Public API: `get_roles_and_permissions_for_user`
- [x] Dependency: `require_permission(...)` للـ Routers
- [x] Permissions مُدمجة في JWT عند تسجيل الدخول
- [ ] HTTP endpoints لإدارة الأدوار/الصلاحيات (لم تُبنَ بعد)
- [ ] تعيين دور تلقائي عند التسجيل

### Alembic Migrations
- [x] migration أولية: tenants, branches, users, refresh_tokens, roles, permissions, role_permissions, user_roles
- [x] migration ثانية: إصلاح PK في user_roles (surrogate id)

### واجهة أمامية (Frontend)
- [x] صفحة رئيسية (Home) مع اختيار نوع المستخدم
- [x] تسجيل صاحب العمل (خطوتان: إنشاء منشأة + تسجيل مدير)
- [x] تسجيل العميل (البحث عن المنشأة + إنشاء حساب)
- [x] صفحة تسجيل الدخول (بالـ slug)
- [x] لوحة تحكم أولية (بيانات الحساب + الأدوار من JWT)

---

## 🔄 المرحلة الثانية: الموديولات الأساسية (قيد التخطيط)

### Access Control — HTTP Endpoints
- [ ] `POST /api/v1/roles` — إنشاء دور
- [ ] `POST /api/v1/roles/{id}/permissions` — إضافة صلاحية لدور
- [ ] `POST /api/v1/users/{id}/roles` — تعيين دور لمستخدم
- [ ] تعيين دور `tenant_admin` تلقائياً عند تسجيل صاحب العمل

### Clinics Module
- [ ] Domain: Clinic entity داخل Branch
- [ ] ORM Model: `clinics`
- [ ] Use Cases: CreateClinic, GetClinics
- [ ] API: `POST/GET /api/v1/clinics`

### Doctors Module
- [ ] ORM Model: `doctors`
- [ ] ربط الأطباء بالعيادات والخدمات
- [ ] API: CRUD doctors

### Patients Module
- [ ] ORM Model: `patients`
- [ ] API: CRUD patients

### Medical Services Module
- [ ] ORM Model: `medical_services`
- [ ] API: CRUD services

### Rooms Module
- [ ] ORM Model: `rooms`
- [ ] API: CRUD rooms

---

## ⏳ المرحلة الثالثة: محرك المواعيد

- [ ] `appointments` module — الأهم (انظر docs/architecture/04-appointment-engine-and-identity.md)
- [ ] أوقات العمل، التعارضات، قوائم الانتظار
- [ ] Domain Events: AppointmentConfirmed, AppointmentCancelled

---

## ⏳ المرحلة الرابعة: الاشتراكات والتقارير

- [ ] `subscriptions` — خطط SaaS، Feature Flags، تجديد
- [ ] `billing_clinical` — فواتير ومدفوعات
- [ ] `dashboard` — KPIs مجمّعة
- [ ] `reporting` — تقارير قابلة للفلترة والتصدير

---

## ⏳ المرحلة الخامسة: الموديولات الداعمة

- [ ] `notifications` — إشعارات (SMTP/Webhook)
- [ ] `audit` — سجل التدقيق
- [ ] `files` — رفع الملفات
- [ ] `settings` — إعدادات قابلة للتوسع

---

## 📌 قيود تقنية ثابتة

```
✅ Python + FastAPI + PostgreSQL + Docker
✅ Modular Monolith (لا Microservices)
❌ Redis / Celery / Kafka / MongoDB / Firebase
❌ GraphQL / gRPC
```
