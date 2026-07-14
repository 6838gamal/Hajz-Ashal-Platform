# 4. محرك المواعيد (Appointment Engine) والهوية والأمان (Identity)

## 4.1 محرك المواعيد — القواعد
1. **Working Hours**: كل طبيب/غرفة له جدول أسبوعي (`working_hours`). لا يُقبل موعد خارج هذا النطاق.
2. **Break Times**: تُمثَّل كسجلات `doctor_time_off(reason='break')` متكررة أو ضمن `working_hours` كفجوات (نموذجان مدعومان، القرار: فجوات داخل `working_hours` لفترات ثابتة يومية، و`doctor_time_off` للاستثناءات).
3. **Vacation / Blocked Time**: `doctor_time_off(reason='vacation'|'blocked')` بمدى زمني، يُستبعد تلقائياً من الفتحات المتاحة.
4. **No Conflict**: `NoOverlapSpecification` في Domain تفحص كل المواعيد النشطة للطبيب/الغرفة في نفس المدى، بالإضافة إلى DB Exclusion Constraint كخط دفاع نهائي (Race Condition عند طلبين متزامنين).
5. **Recurring Appointments**: `recurrence_rule` (JSONB بصيغة تشبه RFC5545 مبسّطة: FREQ, INTERVAL, COUNT/UNTIL). عند الحجز، Use Case منفصل `BookRecurringAppointment` يولّد سلسلة Appointments مرتبطة بـ `recurrence_group_id`، كل واحد يُفحص بنفس القواعد أعلاه؛ فشل أي مثيل لا يوقف الباقي (Best-effort + تقرير بالفتحات التي تعذّر حجزها).
6. **Waiting List**: إذا لم تتوفر فتحة، يُسجَّل الطلب في `waiting_list_entries`. عند إلغاء موعد (`AppointmentCanceled` Event)، Use Case `OfferWaitingSlot` يبحث عن أقرب طلب مطابق ويُرسل عرضاً (Notification) بحالة `offered` مع صلاحية زمنية محدودة.
7. **Reschedule**: Use Case مستقل (لا تعديل مباشر على `start_at`)؛ يُنشئ سجل جديد في `appointment_status_history` وينفّذ نفس فحوصات الحجز على الموعد الجديد، مع الحفاظ على `id` الأصلي (تحديث بدل إنشاء) وربطه بسبب إعادة الجدولة.
8. **Cancellation**: تُحدّث الحالة إلى `canceled` (Soft) مع `canceled_reason` وتُطلق Event لتشغيل قائمة الانتظار والإشعارات.
9. **Confirmation**: انتقال `requested -> confirmed` يدوي (موظف الاستقبال) أو تلقائي (حسب إعدادات Tenant)، يُطلق `AppointmentConfirmed`.
10. **Reminder**: Job داخلي دوري (بدون Celery) — `core` يوفّر **Internal Scheduler** بسيط قائم على `asyncio` (Background Task مسجَّل عند إقلاع FastAPI، يعمل بفاصل زمني ثابت) يفحص المواعيد القادمة ويكتب سجلات في جدول `notifications` (Outbox) لتُعالَج بواسطة Worker داخلي آخر يُرسلها عبر القناة المهيأة (Email/SMS Adapter — Interface فقط في هذه المرحلة).

### Appointment Status Workflow
```
requested --confirm--> confirmed --check_in--> checked_in --complete--> completed
    |                      |                                              
    +--cancel--> canceled <+---------------------cancel----------------- 
    |
    +--(no show at time)--> no_show
```
كل انتقال يُفحص عبر `AppointmentStatusPolicy` (لا يمكن `completed -> confirmed` مثلاً)، وكل انتقال يُسجَّل في `appointment_status_history`.

## 4.2 Identity (المصادقة والتفويض)
- **Authentication**: تسجيل دخول بـ `email + password` (Argon2/Bcrypt Hashing) يُصدر **Access Token (JWT, قصير العمر ~15 دقيقة)** و**Refresh Token (طويل العمر، مخزَّن Hashed في `refresh_tokens`, قابل للإبطال Revocation)**.
- **Claims داخل JWT**: `sub (user_id)`, `tenant_id`, `roles`, `permissions` (مصغّرة/مُجمَّعة عند التوليد لتفادي إعادة الاستعلام في كل طلب)، `exp`, `jti`.
- **Refresh Flow**: Endpoint مخصص يتحقق من `refresh_token` (Hash) وحالته (غير مُبطَل، غير منتهٍ) ثم يصدر زوج Tokens جديد (Rotation: يُبطل القديم فوراً لمنع إعادة الاستخدام).
- **RBAC**: `roles` <-> `permissions` (Many-to-Many)، `users` <-> `roles` (مع تقييد اختياري بـ `branch_id`). قرار الصلاحية يتم عبر `PermissionChecker` Dependency: `Depends(require_permission("appointments.create"))`.
- **Policies**: طبقة إضافية فوق RBAC لقواعد سياقية (مثل: طبيب يرى فقط مواعيده الخاصة حتى لو كانت لديه صلاحية `appointments.read` العامة) — تُنفَّذ كـ Specification يُمرَّر تلقائياً لأي Query في الموديولات ذات الحساسية.
- **Tenant Resolution**: Middleware يستخرج `tenant_id` من JWT ويضعه في `TenantContext` (contextvars) قبل الدخول لأي Route؛ Base Repository يعتمد عليه تلقائياً — يستحيل الوصول لبيانات Tenant آخر عن طريق الخطأ.

## 4.3 اعتبارات الأمان الإضافية
- Rate limiting على Login/Refresh لمنع Brute Force.
- Audit Log لكل عملية حساسة (تسجيل دخول، تغيير صلاحيات، حذف مريض...).
- Password Policy قابلة للتهيئة لكل Tenant (الحد الأدنى للطول، التعقيد).
- CORS و Security Headers تُدار عبر Middleware في `core`.
