# منصة SaaS لإدارة وحجز المواعيد — وثيقة التصميم (المرحلة الأولى)

هذه الوثيقة تغطي **التصميم الكامل** للنظام قبل كتابة أي كود، بحسب طلبك. لا يوجد كود في هذه المرحلة — فقط قرارات معمارية، تصميم قاعدة بيانات، تصميم Modules، وتصميم الطبقات (Layers).

## القيود التقنية المعتمدة
- Python + FastAPI + PostgreSQL + Docker فقط.
- Monolith Modular (وليس Microservices).
- بدون Redis / Celery / RabbitMQ / Kafka / MongoDB / Firebase / Supabase / Elasticsearch / GraphQL / gRPC.
- Clean Architecture + DDD + SOLID + Repository/UnitOfWork + DI + CQRS داخلي عند الحاجة.

## فهرس الوثائق
1. [تحليل النظام والمجالات والموديولات](01-analysis-and-domains.md)
2. [تصميم قاعدة البيانات](02-database-design.md)
3. [تصميم الطبقات: Entities / Value Objects / DTOs / Use Cases / Repositories / Services + تصميم API](03-layers-and-api-design.md)
4. [محرك المواعيد (Appointment Engine) + الهوية والأمان (Identity)](04-appointment-engine-and-identity.md)
5. [Dashboard + Reporting + الاشتراكات (Subscriptions/Billing)](05-dashboard-reporting-subscription.md)
6. [هيكل المجلدات + Docker + Configuration + Deployment](06-folder-structure-and-deployment.md)

## حالة المرحلة
✅ التصميم مكتمل بانتظار مراجعتك.
🚫 لا يوجد كود مكتوب بعد — بحسب تعليماتك الصريحة.

بعد موافقتك على هذا التصميم (أو طلب تعديلات عليه)، ننتقل إلى مرحلة البناء التدريجي: نبدأ بـ Core + Identity + Tenants كأساس، ثم Clinics/Branches/Doctors/Patients، ثم Appointment Engine، ثم Subscriptions/Billing، ثم Dashboard/Reporting.
