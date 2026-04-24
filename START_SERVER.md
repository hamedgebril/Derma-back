# 🚀 تشغيل السيرفر - Quick Start

## ✅ تم حل المشكلة!

المشكلة كانت: `email-validator` مش مثبت في الـvirtual environment

**تم الحل:** ✅ تم تثبيت المكتبة

---

## 🎯 خطوات التشغيل (انسخ والصق)

### 1. فعّل الـVirtual Environment

```bash
venv\Scripts\activate
```

يجب أن ترى `(venv)` قبل الـprompt:
```
(venv) E:\artifictial intelligence\derma_project\backend>
```

### 2. شغّل السيرفر

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. افتح المتصفح

```
http://localhost:8000/docs
```

---

## 📋 الأوامر الكاملة (نسخة واحدة)

```bash
# فعّل venv وشغّل السيرفر
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## ✅ السيرفر شغال لما تشوف:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## 🌐 الروابط المتاحة

بعد تشغيل السيرفر، افتح:

- **Swagger UI (API Docs):**
  ```
  http://localhost:8000/docs
  ```

- **Health Check:**
  ```
  http://localhost:8000/api/v1/health
  ```

- **Readiness Check:**
  ```
  http://localhost:8000/api/v1/ready
  ```

- **Root:**
  ```
  http://localhost:8000/
  ```

---

## 🛑 إيقاف السيرفر

اضغط `Ctrl + C` في الـterminal

---

## 🔄 إعادة التشغيل

لو عملت تغييرات في الكود:
- السيرفر هيعمل reload تلقائي (بسبب `--reload`)
- لو عايز تعيد التشغيل يدوياً:
  1. اضغط `Ctrl + C`
  2. شغّل الأمر تاني: `uvicorn app.main:app --reload`

---

## 💡 نصائح

### استخدم port مختلف لو 8000 مشغول:
```bash
uvicorn app.main:app --reload --port 8001
```

### شغّل بدون reload (أسرع):
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### شغّل مع workers متعددة (Production):
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🧪 اختبار السيرفر

### من المتصفح:
```
http://localhost:8000/docs
```

### من Terminal:
```bash
curl http://localhost:8000/api/v1/health
```

### من PowerShell:
```powershell
Invoke-WebRequest http://localhost:8000/api/v1/health
```

---

## 🎉 كل حاجة شغالة دلوقتي!

السيرفر جاهز للاستخدام. جرب الـAPI من Swagger UI.
