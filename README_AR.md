# Dermavision Backend - واجهة برمجية لتحليل الأمراض الجلدية

Backend جاهز للإنتاج مع FastAPI لتشخيص الأمراض الجلدية بالذكاء الاصطناعي.

> **English Version**: [README.md](README.md) | **دليل التكامل مع الفرونت**: [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)

## نظرة عامة

يوفر هذا الـ backend:
- تشخيص الأمراض الجلدية بالذكاء الاصطناعي باستخدام EfficientNet-B4
- نظام مصادقة كامل بـ JWT
- تتبع سجل التشخيصات
- تقييم جودة الصورة
- رفع وتخزين الصور بشكل آمن

## آخر التحديثات

**توحيد عقد استجابة API التشخيص**

كانت أشكال الاستجابة غير متسقة بين endpoints التشخيص، مما كان يسبب مشاكل في التكامل بين الفرونت والباك. تم حل هذه المشكلة بالكامل. الآن جميع endpoints التشخيص الثلاثة ترجع استجابة موحدة ومنظمة عبر mapper layer مخصصة.

الحقول المضمونة في كل استجابة تشخيص:
- `predicted_label` — نوع المرض المتوقع
- `confidence` — درجة الثقة (0–1)
- `image_quality_score` — درجة جودة الصورة (0–100)
- `image_quality_label` — تصنيف الجودة

الملفات المضافة أو المعدّلة:
- `app/api/v1/schemas/diagnosis_response.py` — نماذج الاستجابة الموحدة
- `app/api/v1/mappers/diagnosis_mapper.py` — طبقة التحويل
- `app/api/v1/endpoints/diagnosis.py` — جميع الـ endpoints محدّثة

## المعمارية

```
API Layer (FastAPI) → Domain Layer (Business Logic) → Infrastructure Layer (DB, ML)
```

- `app/api/` — الـ endpoints، معالجة الطلبات والاستجابات، الـ middleware
- `app/domain/` — منطق العمل (التشخيص، إدارة الملفات)
- `app/infrastructure/` — قاعدة البيانات، موديل الذكاء الاصطناعي
- `app/core/` — الإعدادات، الأمان، الـ logging، الاستثناءات

## المتطلبات

- Python 3.11+
- 2GB+ مساحة حرة (لملفات الموديل)
- SQLite (افتراضي) أو PostgreSQL (للإنتاج)

## الإعداد السريع

### 1. تثبيت المكتبات

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. إعداد ملف الموديل

ضع ملف الموديل في:
```
app/infrastructure/ml/weights/skin_efficientnet_b4_9.pth
```

### 3. إعداد متغيرات البيئة

```bash
cp .env.example .env
```

المتغيرات الأساسية:
```bash
SECRET_KEY=your-secret-key-minimum-32-characters
AUTH_REQUIRED=False        # True في الإنتاج
DATABASE_URL=sqlite:///./skin_analysis.db
MODEL_PATH=./app/infrastructure/ml/weights/skin_efficientnet_b4_9.pth
MODEL_DEVICE=cpu
CORS_ORIGINS=["http://localhost:5173","https://your-frontend.vercel.app"]
```

### 4. تهيئة قاعدة البيانات

```bash
alembic upgrade head
```

### 5. تشغيل السيرفر

```bash
# للتطوير
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# للإنتاج
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

السيرفر يعمل على: http://localhost:8000

## نظام المصادقة

### وضع التطوير (`AUTH_REQUIRED=False`)
- لا يحتاج authentication
- يستخدم user_id=1 افتراضياً
- مناسب للتطوير المحلي

### وضع الإنتاج (`AUTH_REQUIRED=True`)
- يتطلب JWT token صحيح
- يرجع 401 بدون token
- مناسب للإنتاج

### تسجيل حساب جديد

```bash
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123"
}
```

الاستجابة (201):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2026-02-22T10:30:00Z"
}
```

### تسجيل الدخول

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

الاستجابة (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

استخدام الـ token:
```
Authorization: Bearer <access_token>
```

## الـ Endpoints المتاحة

### الصحة والحالة
- `GET /api/v1/health` — فحص صحة السيرفر
- `GET /api/v1/ready` — فحص الجاهزية (موديل الذكاء الاصطناعي + قاعدة البيانات)

### المصادقة
- `POST /api/v1/auth/signup` — إنشاء حساب جديد
- `POST /api/v1/auth/login` — تسجيل الدخول والحصول على JWT

### التشخيص (محمي*)
- `POST /api/v1/diagnosis` — تحليل صورة المرض الجلدي
- `GET /api/v1/history?limit=20` — سجل التشخيصات
- `GET /api/v1/diagnosis/{analysis_id}` — تشخيص محدد بالـ ID

*الـ endpoints المحمية تتطلب authentication فقط عند `AUTH_REQUIRED=True`

## عقد API التشخيص الموحد

جميع endpoints التشخيص الثلاثة ترجع الحقول التالية بشكل مضمون:

| الحقل | النوع | الوصف |
|---|---|---|
| `predicted_label` | string | نوع المرض المتوقع |
| `confidence` | float (0–1) | درجة الثقة |
| `image_quality_score` | int (0–100) | درجة جودة الصورة |
| `image_quality_label` | string | تصنيف الجودة |

### POST /api/v1/diagnosis

الطلب: `multipart/form-data`، حقل `file` (JPG, PNG, HEIC، حد أقصى 10MB)

الاستجابة (201):
```json
{
  "predicted_label": "psoriasis",
  "confidence": 0.92,
  "top_k": [
    { "label": "psoriasis", "confidence": 0.92 },
    { "label": "tinea circinata", "confidence": 0.05 },
    { "label": "healty", "confidence": 0.02 }
  ],
  "image_quality_score": 85,
  "image_quality_label": "Good",
  "analysis_id": 123
}
```

> ملاحظة: `"healty"` هو التسمية كما هي مخزنة في الموديل المدرّب، وتُرجع كما هي.

### GET /api/v1/diagnosis/{analysis_id}

الاستجابة (200):
```json
{
  "id": 123,
  "predicted_label": "psoriasis",
  "confidence": 0.92,
  "all_predictions": [
    { "disease_type": "psoriasis", "probability": 0.92, "confidence_percentage": 92.0, "rank": 1 },
    { "disease_type": "tinea circinata", "probability": 0.05, "confidence_percentage": 5.0, "rank": 2 }
  ],
  "image_quality_score": 85,
  "image_quality_label": "Good",
  "created_at": "2026-02-22T10:30:00Z"
}
```

### GET /api/v1/history

الاستجابة (200):
```json
{
  "analyses": [
    {
      "id": 123,
      "predicted_label": "psoriasis",
      "confidence": 0.92,
      "image_quality_score": 85,
      "image_quality_label": "Good",
      "created_at": "2026-02-22T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 20
}
```

## موديل الذكاء الاصطناعي

- **المعمارية**: EfficientNet-B4
- **حجم الإدخال**: 380×380 بكسل
- **الفئات**: MF، annular lichen، healty، psoriasis، tinea circinata، urticaria

### تقييم جودة الصورة
| الدقة | الدرجة | التصنيف |
|---|---|---|
| ≥1024px | 95 | Excellent |
| ≥512px | 85 | Good |
| ≥256px | 70 | Fair |
| ≥128px | 50 | Poor |
| <128px | 30 | Very Poor |

## إدارة قاعدة البيانات

```bash
alembic upgrade head                                    # تطبيق جميع الـ migrations
alembic downgrade -1                                    # التراجع عن migration واحد
alembic current                                         # الإصدار الحالي
alembic revision --autogenerate -m "description"        # إنشاء migration جديد
```

## حل المشاكل الشائعة

**الموديل لا يعمل**
```bash
# تأكد من وجود الملف
dir app\infrastructure\ml\weights\skin_efficientnet_b4_9.pth
```

**أخطاء المصادقة**
- تأكد من وجود `SECRET_KEY` في `.env`
- تحقق من إعداد `AUTH_REQUIRED`
- الـ token ينتهي بعد 60 دقيقة افتراضياً

**أخطاء CORS**
- أضف رابط الفرونت إلى `CORS_ORIGINS` في `.env` وأعد تشغيل السيرفر

**أخطاء قاعدة البيانات**
```bash
alembic upgrade head
```

**مشاكل رفع الملفات**
- الصيغ المسموحة: JPG, PNG, HEIC
- الحد الأقصى: 10MB
- يجب أن يكون `Content-Type: multipart/form-data`

## الاختبار

```bash
# فحص الصحة
curl http://localhost:8000/api/v1/ready

# تسجيل حساب
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"test123"}'

# تسجيل دخول
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# تشخيص
TOKEN="your-jwt-token"
curl -X POST "http://localhost:8000/api/v1/diagnosis" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_image.jpg"

# السجل
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/history?limit=10"
```

## النشر للإنتاج

### قائمة التحقق قبل النشر

- [ ] `AUTH_REQUIRED=True`
- [ ] `ENVIRONMENT=production`، `DEBUG=False`
- [ ] `SECRET_KEY` قوي (64+ حرف)
- [ ] `DATABASE_URL` للإنتاج (PostgreSQL موصى به)
- [ ] `CORS_ORIGINS` محدّث برابط الفرونت
- [ ] `alembic upgrade head` مُشغَّل
- [ ] HTTPS مفعّل

### Docker

```bash
docker build -t dermavision-api .

docker run -d \
  -p 8000:8000 \
  -e AUTH_REQUIRED=True \
  -e SECRET_KEY=your-secret-key \
  --name dermavision-api \
  dermavision-api
```

توليد SECRET_KEY آمن:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## ميزات الأمان

- تشفير كلمات المرور بـ bcrypt
- مصادقة JWT
- انتهاء صلاحية الـ token قابل للضبط
- التحقق من نوع وحجم الملف
- حماية CORS
- SQLAlchemy ORM (حماية من SQL injection)
- التحقق من المدخلات بـ Pydantic

## توثيق الـ API

عند تشغيل السيرفر:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## التوثيق

- **README.md** — دليل المطور (بالإنجليزية)
- **README_AR.md** — هذا الملف (بالعربية)
- **FRONTEND_INTEGRATION.md** — دليل التكامل مع الفرونت
- **docs_archive/** — التوثيق القديم (للمرجع فقط)

## الرخصة

[Your License Here]
