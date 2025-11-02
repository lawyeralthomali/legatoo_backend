# 🚀 نظام Embeddings - دليل البدء السريع

## ✅ الإعداد السريع (5 دقائق)

### 1. تشغيل Migration

```bash
alembic upgrade head
```

### 2. معالجة البيانات الموجودة

```bash
# معالجة جميع الـ chunks بدون embeddings
python scripts/generate_embeddings_batch.py --pending
```

### 3. اختبار البحث

```python
from app.services.embedding_service import EmbeddingService
from app.db.database import get_db_session

async def test():
    async with get_db_session() as db:
        service = EmbeddingService(db)
        results = await service.find_similar_chunks(
            query="فسخ العقد",
            top_k=5
        )
        for r in results:
            print(f"{r['similarity']:.2%}: {r['content'][:100]}")

# تشغيل
import asyncio
asyncio.run(test())
```

---

## 📌 API Endpoints

### توليد Embeddings

```bash
# لـ document محدد
curl -X POST "http://localhost:8000/api/v1/embeddings/documents/123/generate" \
  -H "Authorization: Bearer YOUR_TOKEN"

# لمجموعة chunks
curl -X POST "http://localhost:8000/api/v1/embeddings/chunks/batch-generate?chunk_ids=1&chunk_ids=2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### البحث الدلالي

```bash
curl -X POST "http://localhost:8000/api/v1/embeddings/search/similar?query=فسخ+العقد&top_k=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### حالة النظام

```bash
# حالة النظام الكامل
curl -X GET "http://localhost:8000/api/v1/embeddings/status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# حالة document محدد
curl -X GET "http://localhost:8000/api/v1/embeddings/documents/123/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📚 التوثيق الكامل

للحصول على التوثيق الشامل، راجع:
**`docs/EMBEDDING_SYSTEM_COMPLETE_GUIDE.md`**

---

## 🎯 الملفات المُنشأة

```
✅ app/services/embedding_service.py          # الخدمة الأساسية
✅ app/routes/embedding_router.py             # API endpoints
✅ app/schemas/embedding.py                   # Pydantic schemas
✅ app/models/legal_knowledge.py              # Model محدث
✅ scripts/generate_embeddings_batch.py       # سكريبت المعالجة
✅ alembic/versions/add_embedding_vector...   # Migration
✅ docs/EMBEDDING_SYSTEM_COMPLETE_GUIDE.md    # التوثيق الكامل
✅ EMBEDDING_QUICK_START.md                   # هذا الملف
```

---

## ✨ جاهز للاستخدام!

النظام الآن مُنشأ بالكامل ويعمل. ابدأ بمعالجة بياناتك:

```bash
python scripts/generate_embeddings_batch.py --status  # عرض الحالة
python scripts/generate_embeddings_batch.py --pending # معالجة البيانات
```

🎉 **تم بنجاح!**
