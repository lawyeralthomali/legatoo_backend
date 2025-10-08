# 🔍 نظام البحث الدلالي - README

## 🚀 البدء السريع

### 1️⃣ التشغيل
```bash
cd C:\Users\Lenovo\my_project
py run.py
```

### 2️⃣ اختبار النظام
```bash
python test_semantic_search.py
```

### 3️⃣ الوصول إلى API
- **Swagger UI**: http://localhost:8000/docs
- **Base URL**: http://localhost:8000/api/v1/search

---

## 📌 API Endpoints

| Endpoint | الوصف |
|----------|-------|
| `POST /search/similar-laws` | بحث في القوانين |
| `POST /search/similar-cases` | بحث في القضايا |
| `POST /search/hybrid` | بحث هجين |
| `GET /search/suggestions` | اقتراحات تلقائية |
| `GET /search/statistics` | إحصائيات |
| `POST /search/clear-cache` | مسح الذاكرة المؤقتة |

---

## 💻 مثال سريع

```python
import requests

url = "http://localhost:8000/api/v1/search/similar-laws"
params = {"query": "فسخ عقد العمل", "top_k": 5}
headers = {"Authorization": "Bearer YOUR_TOKEN"}

response = requests.post(url, params=params, headers=headers)
print(response.json())
```

---

## 📚 التوثيق الكامل

- **دليل شامل**: `docs/SEMANTIC_SEARCH_COMPLETE_GUIDE.md`
- **بدء سريع**: `SEMANTIC_SEARCH_QUICK_START.md`
- **ملخص**: `SEMANTIC_SEARCH_SUMMARY.md`

---

## ✅ المتطلبات

- ✅ Python 3.8+
- ✅ نظام الـ Embeddings مثبت
- ✅ Embeddings تم إنشاؤها للبيانات
- ✅ JWT token للمصادقة

---

## 🎯 الميزات

- ✨ بحث دلالي ذكي (AI-powered)
- 🎯 فلترة متقدمة
- ⚡ أداء محسّن مع caching
- 💡 اقتراحات تلقائية
- 📊 إحصائيات شاملة
- 🌐 دعم كامل للعربية

---

## 🔧 استكشاف الأخطاء

### نتائج فارغة؟
```bash
# تأكد من إنشاء embeddings
py scripts/generate_embeddings_batch.py --pending
```

### بحث بطيء؟
```bash
# امسح الذاكرة المؤقتة
curl -X POST "http://localhost:8000/api/v1/search/clear-cache" \
  -H "Authorization: Bearer TOKEN"
```

---

## 📞 الدعم

- راجع التوثيق الكامل في `docs/`
- تحقق من `logs/app.log` للأخطاء
- استخدم Swagger UI للاختبار

---

**🎉 نظام جاهز للاستخدام!** 🚀
