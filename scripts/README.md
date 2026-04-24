# Backend Testing & Verification Scripts

مجموعة من السكريبتات للتحقق من صحة الـBackend API.

## السكريبتات المتاحة

### 1. audit_routes.py
**الغرض:** فحص جميع الـroutes المسجلة في التطبيق

**الاستخدام:**
```bash
python scripts/audit_routes.py
```

**ماذا يفعل:**
- يعرض جميع الـAPI routes المسجلة
- يتحقق من مطابقتها للقائمة المطلوبة (7 endpoints)
- يكشف أي endpoints قديمة أو غير مرغوبة
- يعطي تقرير نهائي: PASS أو FAIL

**النتيجة المتوقعة:**
```
✅ All required routes are present
✅ No deprecated routes found
Status: ✅ PASS
```

---

### 2. test_api_flow.py
**الغرض:** اختبار الـflow الكامل للـAPI

**الاستخدام:**
```bash
python scripts/test_api_flow.py
```

**ماذا يفعل:**
- يختبر Health endpoints
- يسجل مستخدم جديد (signup)
- يسجل دخول (login)
- يرفع صورة ويحللها (diagnosis)
- يحصل على السجل (history)
- يحصل على تحليل محدد (get by ID)
- يتحقق من أن الـendpoints القديمة ترجع 404

**المتطلبات:**
- السيرفر يجب أن يكون شغال: `uvicorn app.main:app --reload`
- صورة اختبار موجودة في: `uploads/c8199e76-a588-4760-97ea-4815d691731d.jpg`

**النتيجة المتوقعة:**
```
✅ All Tests Passed!
🎉 API is fully functional and clean!
```

---

### 3. verify_api_endpoints.py
**الغرض:** اختبار سريع لجميع الـendpoints

**الاستخدام:**
```bash
python scripts/verify_api_endpoints.py
```

**ماذا يفعل:**
- يختبر Health endpoints
- يختبر Authentication endpoints
- يختبر Diagnosis endpoints
- يتحقق من أن الـendpoints القديمة محذوفة

---

### 4. verify_setup.py
**الغرض:** التحقق من إعداد المشروع

**الاستخدام:**
```bash
python scripts/verify_setup.py
```

**ماذا يفعل:**
- يتحقق من وجود الملفات المطلوبة
- يتحقق من إعدادات البيئة
- يتحقق من قاعدة البيانات
- يتحقق من الموديل

---

### 5. test_auth.py
**الغرض:** اختبار نظام الـAuthentication

**الاستخدام:**
```bash
python scripts/test_auth.py
```

---

### 6. test_inference.py
**الغرض:** اختبار الموديل مباشرة

**الاستخدام:**
```bash
python scripts/test_inference.py
```

---

## الترتيب الموصى به

عند إعداد المشروع لأول مرة:

1. **verify_setup.py** - تحقق من الإعداد
2. **audit_routes.py** - تحقق من الـroutes
3. **test_api_flow.py** - اختبار كامل

عند التطوير:

1. **audit_routes.py** - بعد تعديل الـroutes
2. **test_api_flow.py** - قبل الـcommit

---

## المتطلبات

جميع السكريبتات تتطلب:
- Python 3.11+
- Virtual environment مفعل
- جميع المكتبات مثبتة: `pip install -r requirements.txt`
- السيرفر شغال (للسكريبتات التي تختبر الـAPI)

---

## ملاحظات

- جميع السكريبتات تستخدم `http://localhost:8000` كـbase URL
- يمكن تعديل الـbase URL في كل سكريبت حسب الحاجة
- السكريبتات تستخدم `httpx` للـHTTP requests
- السكريبتات تعطي exit code 0 عند النجاح، 1 عند الفشل

---

## استكشاف الأخطاء

### خطأ: "Connection refused"
**الحل:** تأكد من أن السيرفر شغال:
```bash
uvicorn app.main:app --reload
```

### خطأ: "Module not found"
**الحل:** تأكد من تفعيل الـvirtual environment:
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### خطأ: "Test image not found"
**الحل:** تأكد من وجود صورة اختبار في مجلد uploads/
