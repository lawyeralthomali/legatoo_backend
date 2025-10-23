# نظام رفع ومعالجة الوثائق القانونية مع دعم قاعدة البيانات المزدوجة

## نظرة عامة

تم تطوير نظام شامل لرفع ومعالجة الوثائق القانونية يدعم قاعدة البيانات المزدوجة (SQL + Chroma Vectorstore) مع ضمان التزامن الكامل بينهما.

## الميزات الرئيسية

### 🔄 دعم قاعدة البيانات المزدوجة
- **قاعدة البيانات SQL**: تخزين البيانات المنظمة والعلاقات
- **Chroma Vectorstore**: تخزين الـ embeddings للبحث الدلالي
- **التزامن التلقائي**: جميع العمليات تتم في كلا النظامين معًا

### 🎯 Singleton Pattern
- **VectorstoreManager**: إدارة موحدة للـ embeddings و Chroma
- **منع التكرار**: ضمان وجود نسخة واحدة فقط من كل مكون
- **تحسين الأداء**: تقليل وقت التحميل والذاكرة

### 🛡️ معالجة الأخطاء المتقدمة
- **Rollback تلقائي**: في حالة فشل أي عملية
- **التزامن المضمون**: إما نجاح العملية في كلا النظامين أو فشلها
- **سجلات مفصلة**: تتبع جميع العمليات والأخطاء

### 🔧 المرونة في الإدارة
- **حذف مرن**: يمكن حذف أي جدول بدون كسر نظام RAG
- **تحديث متزامن**: تحديث المحتوى في كلا النظامين
- **مزامنة يدوية**: إمكانية مزامنة النظامين عند الحاجة

## البنية التقنية

### 1. VectorstoreManager (Singleton)
```python
class VectorstoreManager:
    """
    مدير موحد للـ Chroma vectorstore والـ embeddings
    يضمن وجود نسخة واحدة فقط من كل مكون
    """
```

**المكونات:**
- `embeddings`: نموذج الـ embeddings (GATE-AraBert-v1)
- `vectorstore`: مثيل Chroma للبحث الدلالي
- `text_splitter`: مقسم النصوص للـ chunks

### 2. DualDatabaseManager
```python
class DualDatabaseManager:
    """
    مدير العمليات المتزامنة بين SQL و Chroma
    يضمن التزامن الكامل والـ rollback التلقائي
    """
```

**الوظائف الرئيسية:**
- `add_chunk_to_both_databases()`: إضافة chunk لكلا النظامين
- `update_chunk_in_both_databases()`: تحديث chunk في كلا النظامين
- `delete_chunk_from_both_databases()`: حذف chunk من كلا النظامين
- `sync_database_states()`: مزامنة حالة النظامين

### 3. LegalDocumentParser (محدث)
```python
class LegalDocumentParser:
    """
    محلل الوثائق القانونية مع دعم قاعدة البيانات المزدوجة
    """
```

**التحسينات:**
- استخدام `DualDatabaseManager` لجميع العمليات
- metadata محسن للـ Chroma
- معالجة أخطاء متقدمة

### 4. DocumentUploadService (محدث)
```python
class DocumentUploadService:
    """
    خدمة رفع الوثائق مع إدارة قاعدة البيانات المزدوجة
    """
```

**الوظائف الجديدة:**
- `update_chunk_content()`: تحديث محتوى chunk
- `delete_chunk()`: حذف chunk
- `delete_document()`: حذف وثيقة كاملة
- `sync_databases()`: مزامنة النظامين
- `get_database_status()`: حالة النظامين

## API Endpoints الجديدة

### 📊 إدارة قاعدة البيانات
```http
GET /api/v1/documents/database/status
```
**الاستجابة:**
```json
{
  "success": true,
  "data": {
    "sql_database": {
      "documents": 5,
      "law_sources": 3,
      "articles": 150,
      "chunks": 450
    },
    "chroma_database": {
      "chunks": 450
    },
    "synchronization": {
      "sql_chunks": 450,
      "chroma_chunks": 450,
      "sync_status": "synchronized"
    }
  }
}
```

### 🔄 مزامنة النظامين
```http
POST /api/v1/documents/database/sync
```

### ✏️ تحديث Chunk
```http
PUT /api/v1/documents/chunks/{chunk_id}
Content-Type: multipart/form-data

new_content=المحتوى الجديد
new_metadata={"keywords": ["قانون", "عمل"]}
```

### 🗑️ حذف Chunk
```http
DELETE /api/v1/documents/chunks/{chunk_id}
```

### 🗑️ حذف وثيقة كاملة
```http
DELETE /api/v1/documents/documents/{document_id}
```

## Metadata في Chroma

كل chunk في Chroma يحتوي على metadata شامل:

```json
{
  "document_id": 123,
  "chunk_id": 456,
  "chunk_index": 0,
  "tokens_count": 150,
  "verified_by_admin": false,
  "created_at": "2024-01-15T10:30:00",
  "law_source_id": 789,
  "article_id": 101,
  "article_number": "المادة 1",
  "article_title": "تعريفات",
  "law_name": "نظام العمل",
  "law_type": "law",
  "jurisdiction": "المملكة العربية السعودية",
  "issuing_authority": "ملك المملكة العربية السعودية",
  "issue_date": "2023-01-01",
  "document_title": "نظام العمل السعودي",
  "document_category": "law",
  "keywords": ["عمل", "موظف", "راتب"]
}
```

## سير العمل (Workflow)

### 1. رفع وثيقة جديدة
```
1. التحقق من صحة الملف
2. حفظ الملف وحساب الـ hash
3. إنشاء سجل KnowledgeDocument في SQL
4. تحليل المحتوى (JSON parsing)
5. إنشاء LawSource و LawArticle في SQL
6. تقسيم النصوص إلى chunks
7. حفظ كل chunk في SQL و Chroma معًا
8. تحديث حالة الوثيقة إلى 'processed'
```

### 2. تحديث chunk
```
1. التحقق من وجود chunk في SQL
2. تحديث المحتوى في SQL
3. حذف chunk القديم من Chroma
4. إضافة chunk الجديد إلى Chroma
5. التأكد من نجاح العملية في كلا النظامين
```

### 3. حذف وثيقة
```
1. الحصول على جميع chunks للوثيقة
2. حذف جميع chunks من Chroma
3. حذف الوثيقة من SQL (cascade سيتولى chunks)
4. التأكد من نجاح العملية
```

## معالجة الأخطاء

### Rollback التلقائي
```python
try:
    # إضافة إلى SQL
    self.db.add(chunk)
    await self.db.commit()
    
    # إضافة إلى Chroma
    self.vectorstore.add_texts(...)
    
except Exception as e:
    # Rollback تلقائي
    await self.db.rollback()
    logger.error(f"❌ Failed: {e}")
    return False
```

### التزامن المضمون
- إما نجاح العملية في كلا النظامين
- أو فشلها مع rollback كامل
- لا توجد حالة وسطى

## الأداء والتحسينات

### تحسينات الذاكرة
- **Singleton Pattern**: منع تكرار النماذج
- **Batch Processing**: معالجة chunks في مجموعات
- **Lazy Loading**: تحميل النماذج عند الحاجة فقط

### تحسينات السرعة
- **Persistent Storage**: Chroma يحفظ البيانات تلقائياً
- **Indexed Queries**: فهارس محسنة في SQL
- **Connection Pooling**: إدارة اتصالات قاعدة البيانات

## الاختبار والتحقق

### اختبار التزامن
```python
# اختبار إضافة chunk
chunk_id = await add_chunk_to_both_databases(...)
assert chunk_exists_in_sql(chunk_id)
assert chunk_exists_in_chroma(chunk_id)
```

### اختبار Rollback
```python
# محاولة إضافة chunk مع خطأ في Chroma
with pytest.raises(Exception):
    await add_chunk_to_both_databases(invalid_chunk)
assert not chunk_exists_in_sql(chunk_id)
```

## التطوير المستقبلي

### دعم أنواع ملفات إضافية
- **PDF**: استخراج النصوص وتحليل التخطيط
- **DOCX**: معالجة مستندات Word
- **TXT**: تحليل النصوص العادية

### تحسينات البحث
- **Hybrid Search**: دمج البحث النصي والدلالي
- **Reranking**: إعادة ترتيب النتائج
- **Multi-language**: دعم لغات متعددة

### تحسينات الإدارة
- **Batch Operations**: عمليات مجمعة
- **Versioning**: إدارة إصدارات الوثائق
- **Audit Trail**: تتبع جميع التغييرات

## الاستخدام

### رفع وثيقة جديدة
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.json" \
  -F "title=نظام العمل" \
  -F "category=law"
```

### فحص حالة النظامين
```bash
curl -X GET "http://localhost:8000/api/v1/documents/database/status"
```

### مزامنة النظامين
```bash
curl -X POST "http://localhost:8000/api/v1/documents/database/sync"
```

## الخلاصة

تم تطوير نظام شامل ومتطور لرفع ومعالجة الوثائق القانونية مع دعم قاعدة البيانات المزدوجة. النظام يضمن:

✅ **التزامن الكامل** بين SQL و Chroma  
✅ **معالجة أخطاء متقدمة** مع rollback تلقائي  
✅ **مرونة في الإدارة** مع إمكانية الحذف والتحديث  
✅ **أداء محسن** باستخدام Singleton Pattern  
✅ **API شامل** لجميع العمليات  
✅ **توثيق مفصل** واختبارات شاملة  

النظام جاهز للاستخدام الفوري ويمكن توسيعه بسهولة لدعم أنواع ملفات إضافية وميزات متقدمة.
