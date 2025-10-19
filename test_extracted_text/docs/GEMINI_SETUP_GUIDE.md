# 🤖 Gemini AI Setup Guide - دليل إعداد Gemini

## 📋 الخلاصة

**نحتاج كلتا المكتبتين** لأن لهما استخدامات مختلفة:

### ✅ `google-genai` (الأحدث):
- **File API** - لاستخراج النص من الملفات (PDF, DOC, DOCX)
- **Document Processing** - معالجة المستندات
- **Used in**: `ai_gemini_parser.py`, `chunk_processing_service.py`

### ✅ `google-generativeai`:
- **Text Generation API** - للتحليل النصي
- **Gemini Pro** - للمحادثة والتحليل
- **Used in**: `gemini_legal_analyzer.py` (نظام التحليل القانوني الجديد)

---

## 🚀 خطوات الإعداد

### 1️⃣ تثبيت المكتبة المطلوبة

```bash
pip install google-generativeai
```

أو من `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

### 2️⃣ الحصول على Gemini API Key

1. اذهب إلى: https://makersuite.google.com/app/apikey
2. سجل دخول بحساب Google
3. اضغط "Create API Key"
4. انسخ المفتاح

---

### 3️⃣ إعداد Environment Variable

**في Windows (PowerShell)**:
```powershell
$env:GOOGLE_AI_API_KEY="your_api_key_here"
```

**في Windows (Command Prompt)**:
```cmd
set GOOGLE_AI_API_KEY=your_api_key_here
```

**في Linux/Mac**:
```bash
export GOOGLE_AI_API_KEY="your_api_key_here"
```

**أو أنشئ ملف `.env` في المجلد الرئيسي**:
```env
GOOGLE_AI_API_KEY=your_api_key_here
```

---

### 4️⃣ التحقق من التثبيت

```bash
py -c "import google.generativeai as genai; print('✅ Gemini library installed!')"
```

---

## 🧪 اختبار سريع

```python
import google.generativeai as genai
import os

# Configure API
api_key = os.getenv("GOOGLE_AI_API_KEY")
genai.configure(api_key=api_key)

# Test
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("مرحباً")
print(response.text)
```

---

## ⚠️ ملاحظات مهمة

1. **API Key مجاني** لكن له حدود استخدام
2. **لا تشارك API Key** مع أحد
3. **لا تضع API Key** في الكود مباشرة
4. استخدم **environment variables** دائماً

---

## 📊 حدود الاستخدام المجاني

| الميزة | الحد المجاني |
|--------|--------------|
| Requests per minute | 60 |
| Requests per day | 1,500 |
| Tokens per minute | 32,000 |

للاستخدام المكثف، قد تحتاج للترقية لخطة مدفوعة.

---

## 🔧 استكشاف الأخطاء

### خطأ: "Module not found"
```bash
pip install google-generativeai
```

### خطأ: "API key not valid"
- تأكد من نسخ المفتاح بشكل صحيح
- تأكد من تفعيل Generative AI API في Google Cloud Console

### خطأ: "Rate limit exceeded"
- انتظر دقيقة وحاول مرة أخرى
- قلل عدد الطلبات

---

## 📚 موارد إضافية

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Google AI Studio](https://makersuite.google.com/)
- [Python SDK GitHub](https://github.com/google/generative-ai-python)

---

## ✅ جاهز للاستخدام؟

بعد اتباع الخطوات أعلاه، يمكنك:

```bash
# تشغيل السيرفر
py run.py

# اختبار Analysis API
curl -X GET "http://localhost:8000/api/v1/analysis/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

**🎉 الآن أنت جاهز لاستخدام Gemini AI في تطبيقك!**
