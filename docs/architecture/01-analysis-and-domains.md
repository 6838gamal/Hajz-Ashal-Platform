# 1. تحليل النظام والمجالات والموديولات

## 1.1 تحليل النظام
النظام هو **منصة SaaS متعددة المستأجرين (Multi-Tenant)** تبدأ بقطاع العيادات الطبية (حجز وإدارة مواعيد) لكنها مبنية كـ **Modular Monolith** بحيث:
- كل قطاع جديد (مطاعم، صالونات، ورش...) = Module جديد فقط، بدون تعديل Core.
- كل ميزة جديدة (Loyalty, CRM, Accounting...) = Module جديد مستقل.
- العزل بين المستأجرين (Tenants) مضمون على مستوى قاعدة البيانات لا على مستوى التطبيق فقط.

## 1.2 المتطلبات الرئيسية
**وظيفية:**
- تسجيل شركات (Tenants) وإدارة فروع وعيادات متعددة تحت كل شركة.
- إدارة مستخدمين بأدوار وصلاحيات مرنة (RBAC) لكل Tenant.
- حجز مواعيد بدون تعارض، مع أوقات عمل، استراحات، عطلات، وقوائم انتظار.
- إدارة أطباء، مرضى، خدمات طبية، غرف.
- فواتير ومدفوعات لكل موعد/خدمة.
- إشعارات (تذكير بالمواعيد، تأكيد، إلغاء) — Provider-agnostic، بدون بنية تحتية خارجية إلزامية (SMTP/Webhook قابلة للتوصيل لاحقاً).
- تقارير وتحليلات (KPIs، معدلات الحضور/الإلغاء، الإيرادات).
- اشتراكات SaaS: خطط، حدود استخدام، Feature Flags، تجربة مجانية، تجديد.
- سجل تدقيق (Audit Log) لكل العمليات الحساسة.

**غير وظيفية:**
- Tenant Isolation كامل على مستوى الصفوف (Row-Level) في كل الجداول متعددة المستأجرين.
- قابلية التوسع الأفقي (إضافة قطاعات) والرأسي (إضافة ميزات) دون كسر التوافق.
- أداء متوقع لعدد كبير من العيادات/الفروع دون الاعتماد على طوابير خارجية (كل المهام المؤجلة تُدار داخل قاعدة PostgreSQL نفسها عبر جداول Outbox/Jobs، وتُعالج بواسطة Worker داخلي بسيط ضمن نفس الـ Monolith — لا Celery/Redis).
- أمان: JWT + Refresh Tokens + RBAC + Policies + Audit.
- قابلية الاختبار: كل Use Case مستقل وقابل للاختبار بدون DB حقيقية (عبر Repository Interfaces).

## 1.3 Business Domains (Bounded Contexts)
| Domain | المسؤولية |
|---|---|
| Identity & Access | مستخدمون، مصادقة، أدوار، صلاحيات، سياسات |
| Tenancy | الشركات، الفروع، العزل بين المستأجرين |
| Subscription & Billing | خطط الاشتراك، الفواتير، المدفوعات، حدود الاستخدام |
| Scheduling (Appointment Engine) | المواعيد، أوقات العمل، التعارضات، قوائم الانتظار |
| Clinical Directory | الأطباء، المرضى، الخدمات الطبية، الغرف |
| Notifications | تذكيرات وتأكيدات (قناة عامة قابلة للتوصيل) |
| Reporting & Analytics | التقارير، KPIs، لوحة التحكم |
| Audit & Compliance | سجل كل التغييرات الحساسة |
| Files | تخزين وإدارة الملفات المرفقة (تقارير طبية، صور...) |
| Settings | إعدادات كل Tenant/Branch |

## 1.4 قائمة الموديولات (Modules) والمرحلة
### Core (بنية أساسية، ليست Domain عمل)
`core` — Base Entity, Base Repository, Base UseCase, Result Pattern, Pagination, Specifications, Common Exceptions/Middleware/Validation/Security/Responses, Enums, Constants.

### موديولات الأساس المشترك (Platform Modules — يعتمد عليها أي قطاع)
1. `identity` — Users, Authentication, JWT/Refresh Tokens
2. `access_control` — Roles, Permissions, Policies (RBAC)
3. `tenants` — Tenants, Branches
4. `subscriptions` — Plans, Billing Cycle, Feature Flags, Usage Tracking, Trials
5. `notifications` — إشعارات عامة، قابلة للتوصيل بأي مزود مستقبلاً
6. `audit` — Audit Logs
7. `files` — رفع/تخزين الملفات
8. `settings` — إعدادات قابلة للتوسع لكل Tenant
9. `dashboard` — KPIs مجمّعة من الموديولات الأخرى عبر Query Interfaces (بدون اعتماد مباشر على تفاصيلها الداخلية)
10. `reporting` — محرك تقارير عام (Filtering/Sorting/Pagination/Export/Aggregation)

### موديولات قطاع العيادات (Vertical: Healthcare Clinics)
11. `clinics` — بيانات العيادة كوحدة عمل (Business Unit) داخل Branch
12. `doctors` — الأطباء وربطهم بالعيادات/الخدمات
13. `patients` — المرضى
14. `medical_services` — الخدمات الطبية القابلة للحجز
15. `rooms` — الغرف/المقصورات
16. `appointments` — محرك المواعيد (الأهم) — انظر وثيقة 04
17. `billing_clinical` — فواتير ومدفوعات مرتبطة بالمواعيد/الخدمات

### موديولات قطاعات مستقبلية (أمثلة فقط — لا تُبنى الآن)
`restaurants`, `salons`, `training_centers`, `law_firms`, `car_workshops`, `schools`, `hotels`, `real_estate` — كل واحد Module مستقل يعيد استخدام `tenants/identity/access_control/subscriptions/notifications/audit/files/dashboard/reporting` وله Domain خاص به (مثلاً `restaurants` لن يحتاج `doctors/patients` بل `tables/menu_items/reservations`).

### موديولات ميزات إضافية (اختيارية لاحقاً)
`loyalty`, `inventory`, `crm`, `marketing`, `accounting`, `hr`, `ai`, `whatsapp`, `calendar_sync` — كل منها Plug-in Module يُفعَّل عبر `subscriptions.feature_flags` دون تعديل الموديولات الأساسية.

## 1.5 العلاقات بين الموديولات (قواعد صارمة)
- **الاتجاه مسموح فقط من القطاع إلى Platform**: `appointments -> tenants/identity/access_control` مسموح. العكس **ممنوع**.
- **لا استيراد مباشر بين موديولات القطاع نفسه لتفاصيلها الداخلية** (مثلاً `appointments` لا يستورد ORM Models من `doctors`)؛ التواصل يتم عبر:
  - **Domain Events** (مثلاً `AppointmentConfirmed` يُستهلك من `notifications` و`dashboard`).
  - **Application-level Ports/Interfaces** معرّفة في الموديول المستهلك ومُنفَّذة بواسطة Adapter رقيق يستدعي Query محدد من الموديول الآخر (لا يوجد استيراد لكامل الموديول، فقط لواجهة Query صريحة يوفرها الموديول الآخر عبر Public API خاص به، عادة ملف `public_api.py` أو `contracts/`).
- `core` لا يعتمد على أي Module آخر أبداً (اتجاه الاعتماد Core <- كل الموديولات).
- كل Module جديد (قطاع أو ميزة) يُسجَّل ذاتيًا (Self-Registration) عبر نقطة تجميع مركزية (Module Registry) تجمع Routers + Migrations + Event Handlers دون أن يعرف Core تفاصيله.

هذا يضمن: بعد سنة، إضافة قطاع "مطاعم" = إنشاء Module جديد + تسجيله في Registry، بدون لمس Core أو أي Module قائم.
