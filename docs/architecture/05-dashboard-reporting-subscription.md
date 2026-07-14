# 5. Dashboard + Reporting + الاشتراكات (Subscription/Billing)

## 5.1 Dashboard Module
- مستقل بالكامل: لا يمتلك جداول مصدرية خاصة به (باستثناء Cache/Materialized اختياري)، بل يستهلك **Query Ports** يوفرها كل Module عبر `public_api.py` (مثل `AppointmentsModule.get_kpis(tenant_id, date_range)`).
- **KPIs المدعومة**: عدد المواعيد اليوم/الأسبوع، معدل الحضور (`completed / (completed+no_show)`), معدل الإلغاء (`canceled / total`), الإيرادات (من `billing_clinical`/`invoices`), عدد المرضى الجدد، أطباء الأكثر حجزاً.
- **Charts Data**: Endpoints تُعيد بيانات مُجمَّعة زمنياً (يومي/أسبوعي/شهري) جاهزة للرسم في الواجهة الأمامية (Time-series JSON بسيط، بدون منطق رسم في Backend).
- **Recent Activities**: تُقرأ من `audit_logs` مُصفّاة حسب Tenant/Branch.
- **Upcoming Appointments**: Query مباشر لـ `appointments` (Read Model، بدون المرور بكامل الـ Aggregate).
- كل استعلام يُنفَّذ عبر **Read-Only SQL Views/Queries** محسّنة (لا تُستخدم لتعديل البيانات)، وتُخزَّن نتائجها اختيارياً في PostgreSQL Materialized View تُحدَّث دورياً عبر الـ Internal Scheduler عند الحاجة لأداء أعلى — يبقى القرار مؤجلاً لمرحلة القياس الفعلي.

## 5.2 Reporting Module
- محرك تقارير عام وقابل لإعادة الاستخدام من أي قطاع مستقبلي:
  - `ReportDefinition` (Domain): يصف مصدر البيانات (اسم View/Query مسجَّل)، الحقول القابلة للفلترة، الحقول القابلة للفرز.
  - `ReportQueryBuilder` (Application): يبني SQL Query بأمان (Parametrized) من `ReportRequest(filters, sort, date_range, page)`.
  - **Export**: CSV/JSON فوراً (Streaming Response)؛ PDF/Excel عبر Adapter اختياري لاحقاً (Interface محجوزة الآن دون تنفيذ).
  - **Aggregations**: `SUM/COUNT/AVG` عبر Query Builder، مع `GROUP BY` محدود لحقول مُعرَّفة مسبقاً في `ReportDefinition` (لمنع SQL Injection وأعباء أداء غير متوقعة).
- كل Module يسجّل تقاريره الخاصة (`ReportDefinition`) عند الإقلاع في Reporting Registry، فيبقى Reporting عاماً بدون معرفة تفاصيل أي قطاع.

## 5.3 Subscription & Billing (SaaS Core)
- **Plans**: `subscription_plans` (Free/Trial/Pro/Enterprise) بحدود (`limits`: عدد الفروع، عدد المستخدمين، عدد المواعيد شهرياً...) وميزات (`features`: JSONB من مفاتيح Feature Flags).
- **Feature Flags**: `SubscriptionService.has_feature(tenant_id, "loyalty_module")` — تُستخدم في نقاط الدخول لأي Module اختياري (مثل `loyalty`, `crm`) لتفعيل/تعطيل الوصول دون حذف الكود.
- **Usage Tracking**: `usage_counters` تُحدَّث عبر Domain Event Handlers (مثلاً كل `AppointmentBooked` يزيد عداد `appointments_this_month`)؛ `SubscriptionGuard` Dependency يفحص الحد قبل تنفيذ أي Command يزيد الاستهلاك، ويرفض بخطأ `USAGE_LIMIT_EXCEEDED` عند التجاوز.
- **Billing Cycle**: `current_period_start/end` على `subscriptions`، Job دوري (Internal Scheduler) يفحص الاشتراكات المنتهية ويُنشئ Invoice للدورة القادمة (`status=draft`)، وينتقل Tenant إلى `past_due` عند فشل الدفع بعد فترة سماح.
- **Trial**: `trial_ends_at` على `subscriptions`؛ عند الانتهاء بدون ترقية، تنتقل الحالة إلى `canceled` أو `active` بخطة Free افتراضية (قرار تجاري قابل للتهيئة).
- **Renewal**: عملية يدوية (Webhook/Manual Confirmation عبر `payments`) في هذه المرحلة — لا تدمج بوابة دفع خارجية بعد (خارج نطاق القيود التقنية الحالية)، الواجهة (`PaymentGatewayPort`) محجوزة لإضافتها لاحقاً بدون تعديل Domain.
