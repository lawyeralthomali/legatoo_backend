# 🚀 Quick Start - AI Analysis System

## ✅ التثبيت مكتمل!

```
✅ google-generativeai: Installed
✅ App loaded: 178 routes
✅ Analysis system: Ready (needs API key)
```

---

## 🔑 الخطوة التالية: إضافة Gemini API Key

### 1️⃣ احصل على API Key

اذهب إلى: https://makersuite.google.com/app/apikey

### 2️⃣ أضف API Key

**PowerShell**:
```powershell
$env:GOOGLE_AI_API_KEY="your_actual_api_key_here"
```

**أو أنشئ ملف `.env`** في المجلد الرئيسي:
```env
GOOGLE_AI_API_KEY=your_actual_api_key_here
```

### 3️⃣ تحقق من التفعيل

```powershell
py -c "from app.services.gemini_legal_analyzer import GeminiLegalAnalyzer; analyzer = GeminiLegalAnalyzer(); print(f'Enabled: {analyzer.is_enabled()}')"
```

**يجب أن ترى**:
```
✅ Gemini Legal Analyzer initialized successfully
Enabled: True
```

---

## 🚀 تشغيل السيرفر

```powershell
py run.py
```

**أو**:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 اختبار API

### 1️⃣ تحقق من الحالة

```powershell
curl -X GET "http://localhost:8000/api/v1/analysis/status" `
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2️⃣ تحليل سريع

```powershell
curl -X POST "http://localhost:8000/api/v1/analysis/quick" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_JWT_TOKEN" `
  -d '{\"case_text\": \"قضية عمالية تتعلق بفصل تعسفي\"}'
```

### 3️⃣ تحليل هجين (موصى به)

```powershell
curl -X POST "http://localhost:8000/api/v1/analysis/hybrid" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_JWT_TOKEN" `
  -d '{\"case_text\": \"قضية عمالية تتعلق بفصل تعسفي بدون إنذار مسبق\", \"validation_level\": \"standard\"}'
```

---

## 🌐 Swagger UI

افتح المتصفح:
```
http://localhost:8000/docs
```

ثم:
1. اضغط **Authorize** 🔒
2. أدخل: `Bearer YOUR_JWT_TOKEN`
3. جرّب أي endpoint من `/api/v1/analysis/`

---

## 📊 الـ Endpoints المتاحة

| Endpoint | الوصف |
|----------|--------|
| `GET /api/v1/analysis/status` | حالة النظام |
| `POST /api/v1/analysis/comprehensive` | تحليل شامل (Gemini) |
| `POST /api/v1/analysis/hybrid` | تحليل هجين ⭐ |
| `POST /api/v1/analysis/rag` | RAG - أقصى دقة 🎯 |
| `POST /api/v1/analysis/quick` | تحليل سريع |
| `POST /api/v1/analysis/classify` | تصنيف القضية |
| `POST /api/v1/analysis/extract-entities` | استخراج الكيانات |
| `POST /api/v1/analysis/generate-strategy` | توليد استراتيجية |
| `POST /api/v1/analysis/answer-question` | الإجابة على سؤال |

---

## 🐛 استكشاف الأخطاء

### خطأ: "Gemini not enabled"
```powershell
# تأكد من وجود API key
$env:GOOGLE_AI_API_KEY="your_key"
```

### خطأ: "Module not found"
```powershell
py -m pip install -r requirements.txt
```

### خطأ: "Authentication failed"
- تأكد من JWT token صحيح
- تحقق من أن المستخدم مسجل في النظام

---

## 📚 للمزيد

- **الدليل الكامل**: `AI_ANALYSIS_SYSTEM_SUMMARY.md`
- **شرح المكتبات**: `GEMINI_LIBRARIES_EXPLANATION.md`
- **دليل الإعداد**: `GEMINI_SETUP_GUIDE.md`

---

## ✅ Check List

- [x] ✅ تثبيت المكتبات
- [x] ✅ تحميل التطبيق (178 routes)
- [ ] ⏳ إضافة Gemini API Key
- [ ] ⏳ تشغيل السيرفر
- [ ] ⏳ اختبار API

---

**🎉 مبروك! النظام جاهز للاستخدام بمجرد إضافة API Key!**
