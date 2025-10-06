# Upload File Path Migration Fix

## ✅ **FIXED: Removed deprecated `upload_file_path` field**

### **Error:**
```json
{
  "message": "Failed to parse PDF: Failed to process document: Database persistence failed: 'upload_file_path' is an invalid keyword argument for LawSource"
}
```

---

## **Root Cause**

In the database schema update (migration `006_update_legal_knowledge_schema.py`), we removed the `upload_file_path` field from `LawSource` and replaced it with:
- `knowledge_document_id` (Foreign Key to `KnowledgeDocument`)
- `status` (ENUM: 'raw', 'processed', 'indexed')

However, several files in the codebase were still trying to use `upload_file_path`.

---

## **Files Updated**

### **1. Models (Already Fixed)**
✅ `app/models/legal_knowledge.py`
- Removed `upload_file_path` column
- Added `knowledge_document_id` FK
- Added `status` ENUM column

---

### **2. Services**

#### ✅ `app/services/hierarchical_document_processor.py`
**Line 798-799:**
```python
# BEFORE:
upload_file_path=law_source_details.get('upload_file_path') if law_source_details else None

# AFTER:
knowledge_document_id=law_source_details.get('knowledge_document_id') if law_source_details else None,
status='raw'
```

#### ✅ `app/services/legal_knowledge_service.py`
**Lines 72-73 and 120-121:**
```python
# BEFORE (create):
upload_file_path=law_source_data.upload_file_path

# AFTER (create):
knowledge_document_id=law_source_data.knowledge_document_id,
status=law_source_data.status or 'raw'

# BEFORE (response):
"upload_file_path": law_source.upload_file_path,

# AFTER (response):
"knowledge_document_id": law_source.knowledge_document_id,
"status": law_source.status,
```

#### ✅ `app/services/arabic_legal_processor.py`
**Line 109-110:**
```python
# BEFORE:
upload_file_path=file_path

# AFTER:
knowledge_document_id=None,  # TODO: Link to KnowledgeDocument if needed
status='raw'
```

---

### **3. Repositories**

#### ✅ `app/repositories/legal_knowledge_repository.py`
**Method: `create_law_source`**
```python
# BEFORE (parameters):
upload_file_path: Optional[str] = None

# AFTER (parameters):
knowledge_document_id: Optional[int] = None,
status: str = 'raw'

# BEFORE (instantiation):
upload_file_path=upload_file_path

# AFTER (instantiation):
knowledge_document_id=knowledge_document_id,
status=status
```

---

### **4. Schemas**

#### ✅ `app/schemas/legal_knowledge.py`
**Classes: `LawSourceBase` and `LawSourceUpdate`**
```python
# BEFORE:
upload_file_path: Optional[str] = None

# AFTER (LawSourceBase):
knowledge_document_id: Optional[int] = None
status: Optional[str] = Field(default='raw', pattern='^(raw|processed|indexed)$')

# AFTER (LawSourceUpdate):
knowledge_document_id: Optional[int] = None
status: Optional[str] = Field(None, pattern='^(raw|processed|indexed)$')
```

---

## **Migration Path**

### **New Law Upload Flow:**
1. **Upload PDF** → Creates `KnowledgeDocument` with `file_hash` and `file_path`
2. **Create LawSource** → Links to `KnowledgeDocument` via `knowledge_document_id`
3. **Parse Hierarchy** → Status transitions: `raw` → `processed` → `indexed`
4. **Create Chunks** → Each article generates `KnowledgeChunk` records

### **Benefits:**
- ✅ **Centralized file management** via `KnowledgeDocument`
- ✅ **Duplicate detection** using `file_hash` (SHA-256)
- ✅ **Status tracking** for processing pipeline
- ✅ **Audit trail** - documents are never deleted, only LawSources
- ✅ **Multiple sources** can reference the same document

---

## **Status Enum Values**

```python
status = 'raw'        # Initial upload, not yet processed
status = 'processed'  # Hierarchy extracted, chunks created
status = 'indexed'    # AI embeddings generated
```

---

## **Verification**

✅ No linter errors
✅ All services updated
✅ All repositories updated
✅ All schemas updated
✅ Migration script ready

---

## **Next Steps for Testing**

1. **Run Alembic Migration:**
```bash
alembic upgrade head
```

2. **Test Law Upload:**
```bash
curl -X POST "http://localhost:8000/api/v1/laws/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "law_name=Saudi Labor Law" \
  -F "law_type=law" \
  -F "jurisdiction=Saudi Arabia" \
  -F "pdf_file=@law.pdf"
```

3. **Expected Response:**
```json
{
  "success": true,
  "message": "Law uploaded and parsed successfully",
  "data": {
    "law_source": {
      "id": 1,
      "name": "Saudi Labor Law",
      "status": "processed",
      "knowledge_document_id": 1
    },
    "branches": [...],
    "statistics": {
      "total_branches": 5,
      "total_chapters": 15,
      "total_articles": 245,
      "total_chunks": 245
    }
  }
}
```

---

## **Status: ✅ COMPLETE**

All `upload_file_path` references have been successfully replaced with the new schema fields.
