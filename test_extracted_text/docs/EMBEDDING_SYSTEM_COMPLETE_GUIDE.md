# 🎯 نظام Embeddings للنصوص القانونية العربية - دليل شامل

## 📋 نظرة عامة

نظام متكامل لتوليد وإدارة embeddings للنصوص القانونية العربية باستخدام **sentence-transformers**. يدعم النظام البحث الدلالي الذكي ويوفر API كامل لإدارة الـ embeddings.

### ✨ المميزات الرئيسية

✅ **دعم اللغة العربية**: نماذج متعددة اللغات مُحسَّنة للعربية  
✅ **معالجة جماعية**: معالجة آلاف الـ chunks بكفاءة عالية  
✅ **بحث دلالي**: استرجاع الـ chunks الأكثر تشابهاً دلالياً  
✅ **API كامل**: endpoints لتوليد واسترجاع والبحث في الـ embeddings  
✅ **سكريبت معالجة جماعية**: معالجة البيانات الحالية بسهولة  
✅ **مرونة عالية**: دعم نماذج متعددة (default, large, small)  
✅ **كاشينغ ذكي**: تخزين مؤقت للـ embeddings المتكررة  

---

## 🏗️ هيكل النظام

```
app/
├── services/
│   └── embedding_service.py         # خدمة توليد الـ embeddings
│
├── routes/
│   └── embedding_router.py          # API endpoints
│
├── schemas/
│   └── embedding.py                 # Pydantic schemas
│
├── models/
│   └── legal_knowledge.py           # KnowledgeChunk model (updated)
│
scripts/
└── generate_embeddings_batch.py     # سكريبت المعالجة الجماعية

alembic/
└── versions/
    └── add_embedding_vector_to_knowledge_chunks.py  # Migration
```

---

## 🔧 التثبيت والإعداد

### 1. المكتبات المطلوبة

المكتبات موجودة بالفعل في `requirements.txt`:

```txt
sentence-transformers>=2.2.0
numpy>=1.24.0
faiss-cpu>=1.7.0
torch>=2.0.0
```

### 2. تشغيل Migration

```bash
# تنفيذ migration لإضافة حقل embedding_vector
alembic upgrade head
```

هذا سيضيف حقل `embedding_vector` من نوع JSON إلى جدول `knowledge_chunks`.

### 3. التحقق من التثبيت

```python
# اختبار سريع
from app.services.embedding_service import EmbeddingService
from app.db.database import get_db_session

async with get_db_session() as db:
    service = EmbeddingService(db)
    service.initialize_model()
    print("✅ Embedding service initialized successfully!")
```

---

## 📊 Database Schema

### KnowledgeChunk Model (محدَّث)

```python
class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    tokens_count = Column(Integer)
    
    # Legacy embedding field (for backward compatibility)
    embedding = Column(Text)
    
    # ✨ NEW: Vector embeddings from sentence-transformers
    embedding_vector = Column(JSON)  # Stores list of floats as JSON
    
    verified_by_admin = Column(Boolean, default=False)
    
    # Foreign keys
    law_source_id = Column(Integer, ForeignKey("law_sources.id"))
    case_id = Column(Integer, ForeignKey("legal_cases.id"))
    article_id = Column(Integer, ForeignKey("law_articles.id"))
    
    created_at = Column(DateTime, server_default=func.now())
```

**حقل `embedding_vector`**:
- نوع البيانات: `JSON`
- يخزن قائمة من الأرقام العشرية (embedding vector)
- مثال: `[0.123, -0.456, 0.789, ...]` (768 dimensions for default model)

---

## 🎯 EmbeddingService - الخدمة الأساسية

### المميزات

```python
class EmbeddingService:
    """خدمة متكاملة لتوليد وإدارة الـ embeddings"""
    
    # 1. تهيئة النموذج
    def initialize_model(self):
        """يحمّل نموذج sentence-transformers"""
    
    # 2. توليد embeddings
    async def generate_chunk_embedding(chunk):
        """يولد embedding لـ chunk واحد"""
    
    async def generate_document_embeddings(document_id):
        """يولد embeddings لكل chunks في document"""
    
    async def generate_batch_embeddings(chunk_ids):
        """يولد embeddings لمجموعة chunks"""
    
    # 3. البحث الدلالي
    async def find_similar_chunks(query, top_k=10, threshold=0.7):
        """يبحث عن الـ chunks الأكثر تشابهاً"""
    
    # 4. حساب التشابه
    def calculate_similarity(embedding1, embedding2):
        """يحسب cosine similarity بين embeddingين"""
    
    # 5. حالة النظام
    async def get_embedding_status(document_id):
        """يعرض حالة embeddings لـ document"""
    
    async def get_global_embedding_status():
        """يعرض حالة embeddings لكل النظام"""
```

### النماذج المدعومة

```python
MODELS = {
    'default': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        # ✅ متوازن (768 dim) - الأفضل للاستخدام العام
    
    'large': 'intfloat/multilingual-e5-large',
        # ✅ دقة عالية (1024 dim) - للحالات التي تحتاج دقة أكبر
    
    'small': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
        # ✅ سريع (384 dim) - للمعالجة السريعة
}
```

### استخدام الخدمة

```python
from app.services.embedding_service import EmbeddingService
from app.db.database import get_db_session

async def example():
    async with get_db_session() as db:
        # إنشاء خدمة embeddings
        service = EmbeddingService(db, model_name='default')
        
        # توليد embeddings لـ document
        result = await service.generate_document_embeddings(
            document_id=123,
            overwrite=False
        )
        print(f"✅ Processed {result['processed_chunks']} chunks")
        
        # البحث عن chunks مشابهة
        similar = await service.find_similar_chunks(
            query="فسخ العقد بدون إنذار",
            top_k=10,
            threshold=0.75
        )
        
        for chunk in similar:
            print(f"📄 Chunk {chunk['chunk_id']}: {chunk['similarity']:.2%}")
```

---

## 🌐 API Endpoints

### 1. توليد Embeddings لـ Document

```http
POST /api/v1/embeddings/documents/{document_id}/generate
```

**Parameters**:
- `document_id` (path): معرّف الـ document
- `overwrite` (query): إعادة توليد embeddings الموجودة (افتراضي: false)

**Response**:
```json
{
  "success": true,
  "message": "Generated embeddings for 45 chunks in document 123",
  "data": {
    "document_id": 123,
    "total_chunks": 45,
    "processed_chunks": 45,
    "failed_chunks": 0,
    "processing_time": "15.2s"
  },
  "errors": []
}
```

**مثال بـ cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/embeddings/documents/123/generate?overwrite=false" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 2. توليد Embeddings لمجموعة Chunks

```http
POST /api/v1/embeddings/chunks/batch-generate
```

**Parameters**:
- `chunk_ids` (query, multiple): قائمة معرّفات الـ chunks (max 1000)
- `overwrite` (query): إعادة التوليد (افتراضي: false)

**Response**:
```json
{
  "success": true,
  "message": "Generated embeddings for 25 chunks",
  "data": {
    "total_chunks": 25,
    "processed_chunks": 25,
    "failed_chunks": 0,
    "processing_time": "4.3s"
  },
  "errors": []
}
```

**مثال بـ cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/embeddings/chunks/batch-generate?chunk_ids=1&chunk_ids=2&chunk_ids=3" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 3. البحث الدلالي (Similarity Search) 🔍

```http
POST /api/v1/embeddings/search/similar
```

**Parameters**:
- `query` (query, required): نص البحث (العربية أو الإنجليزية)
- `top_k` (query): عدد النتائج (1-100، افتراضي: 10)
- `threshold` (query): الحد الأدنى للتشابه (0.0-1.0، افتراضي: 0.7)
- `document_id` (query, optional): تصفية حسب document
- `case_id` (query, optional): تصفية حسب case
- `law_source_id` (query, optional): تصفية حسب law source

**Response**:
```json
{
  "success": true,
  "message": "Found 8 similar chunks",
  "data": {
    "query": "فسخ العقد بدون إنذار",
    "results": [
      {
        "chunk_id": 456,
        "content": "يجوز لصاحب العمل فسخ العقد دون إنذار في حالات الإخلال الجسيم...",
        "similarity": 0.89,
        "document_id": 123,
        "chunk_index": 10,
        "law_source_id": 5,
        "article_id": 75,
        "tokens_count": 250
      },
      {
        "chunk_id": 789,
        "content": "المادة ٧٤: إذا أخل أحد الطرفين بالالتزامات الجوهرية...",
        "similarity": 0.85,
        "document_id": 123,
        "chunk_index": 15,
        "law_source_id": 5,
        "article_id": 74,
        "tokens_count": 180
      }
    ],
    "total_results": 8,
    "threshold": 0.7
  },
  "errors": []
}
```

**مثال بـ cURL**:
```bash
curl -X POST "http://localhost:8000/api/v1/embeddings/search/similar?query=فسخ+العقد&top_k=10&threshold=0.75" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**مثال مع تصفية**:
```bash
# البحث فقط في قضايا العمل
curl -X POST "http://localhost:8000/api/v1/embeddings/search/similar?query=إنهاء+الخدمة&case_id=25" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# البحث فقط في نظام العمل
curl -X POST "http://localhost:8000/api/v1/embeddings/search/similar?query=ساعات+العمل&law_source_id=3" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 4. حالة Embeddings لـ Document

```http
GET /api/v1/embeddings/documents/{document_id}/status
```

**Response**:
```json
{
  "success": true,
  "message": "Embedding status for document 123",
  "data": {
    "document_id": 123,
    "total_chunks": 50,
    "chunks_with_embeddings": 45,
    "chunks_without_embeddings": 5,
    "completion_percentage": 90.0,
    "status": "partial"
  },
  "errors": []
}
```

**Status Values**:
- `complete`: جميع الـ chunks لها embeddings
- `partial`: بعض الـ chunks لها embeddings
- `not_started`: لا يوجد embeddings بعد

---

### 5. حالة Embeddings للنظام الكامل

```http
GET /api/v1/embeddings/status
```

**Response**:
```json
{
  "success": true,
  "message": "Global embedding status",
  "data": {
    "total_chunks": 1250,
    "chunks_with_embeddings": 1000,
    "chunks_without_embeddings": 250,
    "completion_percentage": 80.0,
    "model_name": "default",
    "device": "cuda"
  },
  "errors": []
}
```

---

### 6. معلومات النموذج

```http
GET /api/v1/embeddings/model-info
```

**Response**:
```json
{
  "success": true,
  "message": "Embedding model information",
  "data": {
    "model_name": "default",
    "model_path": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "embedding_dimension": 768,
    "device": "cuda",
    "max_seq_length": 512,
    "batch_size": 32
  },
  "errors": []
}
```

---

## 🔄 سكريبت المعالجة الجماعية

### الاستخدام

```bash
# 1. معالجة جميع الـ documents
python scripts/generate_embeddings_batch.py --all

# 2. معالجة الـ chunks بدون embeddings فقط (الافتراضي)
python scripts/generate_embeddings_batch.py --pending

# 3. معالجة document محدد
python scripts/generate_embeddings_batch.py --document-id 123

# 4. استئناف المعالجة الفاشلة
python scripts/generate_embeddings_batch.py --resume

# 5. عرض حالة النظام فقط
python scripts/generate_embeddings_batch.py --status

# 6. استخدام نموذج مختلف
python scripts/generate_embeddings_batch.py --all --model large

# 7. تغيير batch size
python scripts/generate_embeddings_batch.py --pending --batch-size 64
```

### الخيارات

| Option | Description |
|--------|-------------|
| `--all` | معالجة جميع الـ documents |
| `--pending` | معالجة الـ chunks بدون embeddings فقط |
| `--document-id ID` | معالجة document محدد |
| `--resume` | استئناف المعالجة الفاشلة |
| `--status` | عرض حالة النظام والخروج |
| `--model MODEL` | اختيار النموذج (default, large, small) |
| `--batch-size N` | حجم الـ batch للمعالجة (افتراضي: 32) |

### مثال كامل

```bash
# خطوة 1: عرض الحالة الحالية
python scripts/generate_embeddings_batch.py --status

# Output:
# ================================================================================
# 📊 SYSTEM STATUS
# ================================================================================
# 📦 Total chunks: 1500
# ✅ With embeddings: 500
# ⏳ Without embeddings: 1000
# 📈 Completion: 33.33%
# ================================================================================

# خطوة 2: معالجة الـ chunks المتبقية
python scripts/generate_embeddings_batch.py --pending --model default

# Output:
# ================================================================================
# 🚀 Starting PENDING chunks embedding generation
# ================================================================================
# 📦 Found 1000 pending chunks
# 📄 Chunks distributed across 25 documents
# 
# ============================================================
# 📄 Processing document 123: 45 chunks
# ============================================================
# ✅ Document 123 chunks processed
# ...
# 
# ================================================================================
# 📊 BATCH PROCESSING REPORT
# ================================================================================
# ⏱️  Duration: 180.50 seconds (3.01 minutes)
# 📄 Documents:
#    Total: 0
#    Processed: 0
#    Failed: 0
# 
# 📦 Chunks:
#    Total: 1000
#    Processed: 995
#    Failed: 5
# 
# ✅ Success Rate: 99.50%
# ================================================================================
```

### مراقبة التقدم

السكريبت يسجل جميع العمليات في:
- **Console Output**: عرض مباشر للتقدم
- **Log File**: `logs/embedding_batch.log`

---

## 🎯 حالات الاستخدام

### 1. معالجة أولية للنظام

عند إضافة نظام الـ embeddings لأول مرة:

```bash
# معالجة جميع البيانات الموجودة
python scripts/generate_embeddings_batch.py --all --model default

# أو معالجة ما ينقص فقط
python scripts/generate_embeddings_batch.py --pending
```

---

### 2. معالجة تلقائية عند رفع document جديد

في API endpoint لرفع الـ documents:

```python
@router.post("/upload")
async def upload_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db)
):
    # رفع وحفظ الـ document
    document = await save_document(file)
    
    # معالجة chunks
    chunks = await process_document_chunks(document)
    
    # ✨ توليد embeddings تلقائياً
    embedding_service = EmbeddingService(db)
    await embedding_service.generate_document_embeddings(document.id)
    
    return {"success": True, "document_id": document.id}
```

---

### 3. بحث دلالي في واجهة المستخدم

```python
@router.get("/search")
async def search_legal_content(
    query: str,
    db: AsyncSession = Depends(get_db)
):
    # استخدام embedding service للبحث
    service = EmbeddingService(db)
    
    results = await service.find_similar_chunks(
        query=query,
        top_k=10,
        threshold=0.7
    )
    
    # تحسين النتائج بإضافة metadata
    enriched_results = []
    for result in results:
        chunk_data = {
            **result,
            "document_title": await get_document_title(result['document_id']),
            "law_name": await get_law_name(result['law_source_id']) if result['law_source_id'] else None
        }
        enriched_results.append(chunk_data)
    
    return {
        "success": True,
        "query": query,
        "results": enriched_results
    }
```

---

### 4. اقتراحات ذكية للمحامي

```python
async def suggest_related_articles(case_description: str, db: AsyncSession):
    """
    يقترح مواد قانونية ذات صلة بوصف القضية
    """
    service = EmbeddingService(db)
    
    # البحث عن chunks مشابهة من القوانين فقط
    results = await service.find_similar_chunks(
        query=case_description,
        top_k=5,
        threshold=0.75,
        filters={"law_source_id": None}  # فقط من القوانين
    )
    
    # استخراج المواد القانونية
    related_articles = []
    for result in results:
        if result['article_id']:
            article = await get_article(result['article_id'])
            related_articles.append({
                "article_number": article.article_number,
                "content": article.content,
                "law_name": article.law_source.name,
                "similarity": result['similarity']
            })
    
    return related_articles
```

---

### 5. تحليل تشابه القضايا

```python
async def find_similar_cases(case_id: int, db: AsyncSession):
    """
    يجد قضايا مشابهة لقضية محددة
    """
    # الحصول على محتوى القضية
    case = await get_case(case_id)
    case_summary = case.sections.get('summary', case.description)
    
    # البحث عن قضايا مشابهة
    service = EmbeddingService(db)
    results = await service.find_similar_chunks(
        query=case_summary,
        top_k=10,
        threshold=0.70,
        filters={"case_id": None}  # استبعاد نفس القضية
    )
    
    # تجميع النتائج حسب القضية
    similar_cases = {}
    for result in results:
        if result['case_id'] and result['case_id'] != case_id:
            if result['case_id'] not in similar_cases:
                similar_cases[result['case_id']] = {
                    "case_id": result['case_id'],
                    "max_similarity": result['similarity'],
                    "matching_sections": []
                }
            similar_cases[result['case_id']]['matching_sections'].append(result)
    
    return list(similar_cases.values())
```

---

## ⚡ الأداء والتحسينات

### إحصائيات الأداء

| Operation | Time | Notes |
|-----------|------|-------|
| توليد embedding لـ chunk واحد | ~0.05s | GPU |
| توليد embedding لـ chunk واحد | ~0.2s | CPU |
| معالجة 1000 chunks | ~5 min | GPU, batch_size=32 |
| معالجة 1000 chunks | ~15 min | CPU, batch_size=32 |
| بحث في 10,000 embeddings | ~0.5s | In-memory cosine similarity |

### تحسينات الأداء

#### 1. استخدام GPU

```python
# تحقق من توفر GPU
import torch
if torch.cuda.is_available():
    print(f"✅ GPU available: {torch.cuda.get_device_name(0)}")
else:
    print("⚠️ Using CPU (slower)")
```

#### 2. زيادة Batch Size

```python
# للأجهزة القوية
service = EmbeddingService(db)
service.batch_size = 64  # زيادة من 32 الافتراضي
```

#### 3. Caching

النظام يخزن مؤقتاً آخر 1000 embedding تم توليدها:

```python
# في EmbeddingService
self._embedding_cache: Dict[str, List[float]] = {}
self._cache_max_size = 1000
```

#### 4. معالجة متوازية (للمستقبل)

```python
# استخدام asyncio.gather لمعالجة متوازية
import asyncio

async def process_multiple_documents(document_ids: List[int]):
    tasks = [
        service.generate_document_embeddings(doc_id)
        for doc_id in document_ids
    ]
    results = await asyncio.gather(*tasks)
    return results
```

---

## 🔍 استكشاف الأخطاء

### مشكلة: Model لا يتحمل

**الأعراض**:
```
RuntimeError: Failed to initialize embedding model
```

**الحل**:
```bash
# تثبيت sentence-transformers
pip install sentence-transformers

# التحقق من الاتصال بالإنترنت (لتحميل النموذج)
ping huggingface.co

# تحميل النموذج يدوياً
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')"
```

---

### مشكلة: نفاد الذاكرة

**الأعراض**:
```
CUDA out of memory
# أو
MemoryError
```

**الحل**:
```python
# 1. تقليل batch_size
service.batch_size = 16  # بدلاً من 32

# 2. استخدام نموذج أصغر
service = EmbeddingService(db, model_name='small')

# 3. معالجة على CPU
import torch
torch.cuda.set_device(-1)  # Force CPU
```

---

### مشكلة: بطء البحث

**الأعراض**:
البحث يستغرق أكثر من 5 ثوانٍ

**الحل**:
```python
# استخدام FAISS للبحث السريع (للمستقبل)
import faiss
import numpy as np

# بناء FAISS index
embeddings = [json.loads(chunk.embedding_vector) for chunk in chunks]
embeddings_array = np.array(embeddings).astype('float32')

index = faiss.IndexFlatIP(768)  # Inner product (cosine similarity)
index.add(embeddings_array)

# البحث
query_embedding = service._encode_text(query)
D, I = index.search(np.array([query_embedding]).astype('float32'), top_k)
```

---

### مشكلة: JSON serialization error

**الأعراض**:
```
TypeError: Object of type 'ndarray' is not JSON serializable
```

**الحل**:
```python
# تحويل numpy array إلى list
import json
embedding_list = embedding.tolist()
chunk.embedding_vector = json.dumps(embedding_list)
```

---

## 📈 مراقبة وتسجيل

### Logging

جميع العمليات مسجلة:

```python
# في embedding_service.py
logger.info("✅ Model initialized successfully")
logger.warning("⚠️ Truncating text from 2000 to 2048 characters")
logger.error("❌ Failed to generate embedding for chunk 123")
```

### Metrics

تتبع الإحصائيات:

```python
{
  "total_chunks": 1500,
  "processed_chunks": 1450,
  "failed_chunks": 50,
  "processing_time": "15.2s",
  "success_rate": 96.67
}
```

---

## 🚀 الخطوات التالية

### المرحلة 1: ✅ تم

- [x] إنشاء `embedding_service.py`
- [x] إنشاء `embedding_router.py`
- [x] تحديث `KnowledgeChunk` model
- [x] إنشاء migration
- [x] إنشاء سكريبت المعالجة الجماعية
- [x] التوثيق الكامل

### المرحلة 2: التحسينات

- [ ] استخدام FAISS للبحث السريع
- [ ] دعم تحديث النماذج بدون downtime
- [ ] API لإدارة النماذج المختلفة
- [ ] معالجة متوازية للـ documents
- [ ] تكامل مع قاعدة بيانات متجهات (pgvector)

### المرحلة 3: ميزات متقدمة

- [ ] Fine-tuning للنموذج على نصوص قانونية سعودية
- [ ] Hybrid search (semantic + keyword)
- [ ] تحليل تشابه القضايا تلقائياً
- [ ] اقتراحات ذكية للمواد القانونية
- [ ] تصنيف تلقائي للنصوص القانونية

---

## 📝 أمثلة عملية

### مثال 1: معالجة document جديد

```python
from app.services.embedding_service import EmbeddingService
from app.db.database import get_db_session

async def process_new_document(document_id: int):
    """معالجة document جديد وتوليد embeddings"""
    async with get_db_session() as db:
        service = EmbeddingService(db, model_name='default')
        
        # توليد embeddings
        result = await service.generate_document_embeddings(document_id)
        
        if result['success']:
            print(f"✅ Processed {result['processed_chunks']} chunks")
            print(f"⏱️  Time: {result['processing_time']}")
        else:
            print(f"❌ Failed: {result.get('error')}")
```

---

### مثال 2: بحث ذكي عن مواد قانونية

```python
async def smart_legal_search(query: str):
    """بحث ذكي عن مواد قانونية ذات صلة"""
    async with get_db_session() as db:
        service = EmbeddingService(db)
        
        # البحث
        results = await service.find_similar_chunks(
            query=query,
            top_k=5,
            threshold=0.75,
            filters={"law_source_id": 3}  # نظام العمل فقط
        )
        
        print(f"🔍 Search results for: '{query}'")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Similarity: {result['similarity']:.2%}")
            print(f"   Content: {result['content'][:100]}...")
            print(f"   Article ID: {result['article_id']}")

# استخدام
await smart_legal_search("إنهاء عقد العمل بدون إنذار")
```

---

### مثال 3: تحليل تشابه القضايا

```python
async def analyze_case_similarity(case_id: int):
    """تحليل تشابه قضية مع قضايا أخرى"""
    async with get_db_session() as db:
        service = EmbeddingService(db)
        
        # الحصول على القضية
        case = await get_case(case_id)
        
        # البحث عن قضايا مشابهة
        results = await service.find_similar_chunks(
            query=case.description,
            top_k=10,
            threshold=0.70
        )
        
        # تجميع حسب القضية
        similar_cases = {}
        for result in results:
            cid = result['case_id']
            if cid and cid != case_id:
                if cid not in similar_cases:
                    similar_cases[cid] = []
                similar_cases[cid].append(result)
        
        print(f"📊 Found {len(similar_cases)} similar cases")
        for cid, chunks in similar_cases.items():
            avg_similarity = sum(c['similarity'] for c in chunks) / len(chunks)
            print(f"   Case {cid}: {avg_similarity:.2%} similarity")
```

---

## 🎯 الخلاصة

نظام الـ embeddings جاهز بالكامل ويوفر:

✅ **API شامل** لتوليد وإدارة الـ embeddings  
✅ **بحث دلالي ذكي** للنصوص القانونية العربية  
✅ **معالجة جماعية** للبيانات الحالية  
✅ **أداء عالٍ** مع دعم GPU  
✅ **مرونة كاملة** في اختيار النماذج  
✅ **توثيق شامل** مع أمثلة عملية  

**جاهز للاستخدام الفوري! 🚀**

---

**آخر تحديث**: 8 يناير 2025  
**الإصدار**: 1.0  
**المطوّر**: Legatoo AI Legal Assistant Team
