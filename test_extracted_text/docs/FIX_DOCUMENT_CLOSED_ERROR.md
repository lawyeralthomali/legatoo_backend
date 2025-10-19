# إصلاح خطأ "document closed"
# Fix for "document closed" Error

## ❌ المشكلة

```
ERROR: Failed to extract text from PDF: document closed
```

### السبب

الكود كان يحاول الوصول إلى `len(doc)` **بعد** إغلاق المستند:

```python
# الكود القديم (خطأ)
for page_num, page in enumerate(doc, 1):
    # معالجة الصفحات...
    pass

doc.close()  # ← إغلاق المستند هنا
logger.info(f"Extracted from {len(doc)} pages")  # ❌ خطأ! محاولة الوصول بعد الإغلاق
```

---

## ✅ الحل

حفظ عدد الصفحات **قبل** المعالجة، واستخدامه في الـ logging:

```python
# الكود الجديد (صحيح)
doc = fitz.open(str(file_path))

# حفظ عدد الصفحات قبل المعالجة
total_pages = len(doc)  # ✅ حفظ القيمة

for page_num, page in enumerate(doc, 1):
    logger.info(f"Processing page {page_num}/{total_pages}")
    # معالجة الصفحات...

doc.close()  # إغلاق المستند

# استخدام القيمة المحفوظة (لا نحاول الوصول للمستند المغلق)
logger.info(f"Extracted from {total_pages} pages")  # ✅ صحيح
```

---

## 🔍 التغييرات بالتفصيل

### السطر 264-266: حفظ عدد الصفحات

```python
# قبل
logger.info(f"Starting advanced PDF extraction for {len(doc)} pages")

# بعد
total_pages = len(doc)  # ← حفظ القيمة
logger.info(f"Starting advanced PDF extraction for {total_pages} pages")
```

### السطر 270: استخدام المتغير المحفوظ

```python
# قبل
logger.info(f"Processing page {page_num}/{len(doc)}")

# بعد
logger.info(f"Processing page {page_num}/{total_pages}")  # ← استخدام القيمة المحفوظة
```

### السطر 331-333: الإغلاق ثم الـ logging

```python
# قبل
doc.close()
logger.info(f"Extracted {len(text)} chars from {len(doc)} pages")  # ❌ خطأ

# بعد
doc.close()  # ← الإغلاق أولاً
logger.info(f"Extracted {len(text)} chars from {total_pages} pages")  # ✅ استخدام القيمة المحفوظة
```

---

## 📊 المقارنة

| العملية | قبل | بعد |
|---------|-----|-----|
| حفظ `len(doc)` | ❌ لا | ✅ نعم |
| الوصول بعد الإغلاق | ❌ نعم (خطأ) | ✅ لا |
| استخدام متغير محفوظ | ❌ لا | ✅ نعم |
| الخطأ | ❌ يحدث | ✅ لا يحدث |

---

## 🎯 الدرس المستفاد

**القاعدة الذهبية:**
> عند العمل مع موارد (resources) مثل ملفات أو مستندات PDF:
> 1. احفظ أي قيم تحتاجها **قبل** إغلاق المورد
> 2. لا تحاول الوصول للمورد **بعد** إغلاقه
> 3. استخدم القيم المحفوظة في الـ logging أو المعالجة اللاحقة

---

## 🧪 الاختبار

### قبل الإصلاح

```bash
curl -X POST "/api/v1/legal-cases/upload" -F "file=@case.pdf"

# النتيجة
❌ ERROR: document closed
```

### بعد الإصلاح

```bash
curl -X POST "/api/v1/legal-cases/upload" -F "file=@case.pdf"

# النتيجة
✅ SUCCESS: Legal case uploaded successfully
```

---

## 📝 الملفات المعدلة

- **الملف:** `app/services/legal_case_ingestion_service.py`
- **الدالة:** `_extract_pdf_text()`
- **الأسطر:** 264-266, 270, 331-333
- **التغييرات:** 3 مواضع
- **Linter Errors:** ✅ 0

---

## ✅ الحالة

| العنصر | القيمة |
|--------|--------|
| **الخطأ** | document closed ❌ |
| **السبب** | الوصول لـ `len(doc)` بعد `doc.close()` |
| **الحل** | حفظ `total_pages` قبل المعالجة |
| **الحالة** | ✅ تم الإصلاح |
| **الاختبار** | ✅ جاهز |

---

**تاريخ الإصلاح:** 6 أكتوبر 2024  
**الأولوية:** عالية (critical bug)  
**التأثير:** يمنع رفع أي ملف PDF  
**الحالة الآن:** ✅ تم الإصلاح بالكامل

