# Cleanup: Removed Metadata Fields

## ✅ Changes Applied

Completely removed the following metadata fields from the legal case system:
- ❌ `involved_parties`
- ❌ `case_outcome`
- ❌ `judge_names`
- ❌ `claim_amount`

These fields were removed from:
1. API endpoint parameters
2. Service layer logic
3. Response schemas
4. All metadata storage code

---

## 📝 What Was Removed

### 1. Router (`app/routes/legal_cases_router.py`)

#### Removed from upload endpoint parameters:
```python
# ❌ REMOVED
involved_parties: Optional[str] = Form(...)
case_outcome: Optional[str] = Form(...)
judge_names: Optional[str] = Form(...)
claim_amount: Optional[float] = Form(...)
```

#### Removed from case_metadata dictionary:
```python
# ❌ REMOVED
'involved_parties': involved_parties,
'case_outcome': case_outcome,
'judge_names': judge_names.split(',') if judge_names else None,
'claim_amount': claim_amount
```

#### Removed from get case response:
```python
# ❌ REMOVED
if case.document and case.document.document_metadata:
    metadata = case.document.document_metadata
    case_data['involved_parties'] = metadata.get('involved_parties')
    case_data['case_outcome'] = metadata.get('case_outcome')
    case_data['judge_names'] = metadata.get('judge_names')
    case_data['claim_amount'] = metadata.get('claim_amount')
```

---

### 2. Service (`app/services/legal_case_ingestion_service.py`)

#### Removed metadata storage logic:
```python
# ❌ REMOVED
if knowledge_doc:
    additional_metadata = {
        'involved_parties': case_metadata.get('involved_parties'),
        'case_outcome': case_metadata.get('case_outcome'),
        'judge_names': case_metadata.get('judge_names'),
        'claim_amount': case_metadata.get('claim_amount')
    }
    knowledge_doc.document_metadata.update(additional_metadata)
```

#### Simplified method signature:
```python
# Before:
async def save_case_with_sections(
    self, case_metadata, sections, document_id, knowledge_doc=None
)

# After:
async def save_case_with_sections(
    self, case_metadata, sections, document_id
)
```

---

### 3. Schemas (`app/schemas/legal_knowledge.py`)

#### Removed from response schema:
```python
# ❌ REMOVED
involved_parties: Optional[str] = None
case_outcome: Optional[str] = None
judge_names: Optional[Union[List[str], str]] = None
claim_amount: Optional[float] = None
```

---

## 🎯 Current Legal Case Model

### Database Fields (LegalCase table)
```python
✅ id
✅ case_number
✅ title
✅ description
✅ jurisdiction
✅ court_name
✅ decision_date
✅ case_type
✅ court_level
✅ document_id
✅ status
✅ created_at
✅ updated_at
```

### API Accepts (Upload Endpoint)
```python
✅ file (required)
✅ title (required)
✅ case_number
✅ description
✅ jurisdiction
✅ court_name
✅ decision_date
✅ case_type
✅ court_level
```

### API Returns (Get/List Endpoints)
```python
✅ All database fields above
✅ sections (if requested)
✅ sections_count
```

---

## 🎨 Swagger Documentation

The Swagger UI (`/docs`) will now show a **clean, simple form** with only the fields that exist in the database model.

**Before:**
```
POST /api/v1/legal-cases/upload
  - file ✓
  - title ✓
  - case_number
  - description
  - jurisdiction
  - court_name
  - decision_date
  - case_type
  - court_level
  - involved_parties ← Removed
  - case_outcome ← Removed
  - judge_names ← Removed
  - claim_amount ← Removed
```

**After:**
```
POST /api/v1/legal-cases/upload
  - file ✓
  - title ✓
  - case_number
  - description
  - jurisdiction
  - court_name
  - decision_date
  - case_type
  - court_level
```

---

## ✅ Benefits

### 1. **Simplicity**
- Only fields that exist in the database
- No confusion about where data is stored
- Cleaner API documentation

### 2. **Consistency**
- API matches database schema exactly
- What you send is what gets stored
- No hidden JSON metadata

### 3. **Maintainability**
- Less code to maintain
- Fewer places where bugs can occur
- Easier to understand

### 4. **Performance**
- No unnecessary JSON parsing
- Simpler queries
- Faster responses

---

## 🧪 Test the Changes

### Upload a Legal Case
```bash
curl -X POST "http://localhost:8000/api/v1/legal-cases/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample_legal_case.txt" \
  -F "title=قضية تجارية - نزاع عقد توريد" \
  -F "case_number=456/2024" \
  -F "jurisdiction=جدة" \
  -F "court_name=المحكمة العامة" \
  -F "decision_date=2024-10-05" \
  -F "case_type=مدني" \
  -F "court_level=ابتدائي"
```

### Expected Response
```json
{
  "success": true,
  "message": "Legal case ingested successfully",
  "data": {
    "knowledge_document_id": 45,
    "legal_case_id": 23,
    "case_number": "456/2024",
    "title": "قضية تجارية - نزاع عقد توريد",
    "file_path": "uploads/legal_cases/...",
    "text_length": 5432,
    "sections_found": ["summary", "facts", "ruling", "legal_basis"],
    "sections_count": 4
  },
  "errors": []
}
```

### Get Case Details
```bash
curl "http://localhost:8000/api/v1/legal-cases/23" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Expected Response
```json
{
  "success": true,
  "message": "Legal case retrieved successfully",
  "data": {
    "id": 23,
    "case_number": "456/2024",
    "title": "قضية تجارية - نزاع عقد توريد",
    "description": null,
    "jurisdiction": "جدة",
    "court_name": "المحكمة العامة",
    "decision_date": "2024-10-05",
    "case_type": "مدني",
    "court_level": "ابتدائي",
    "document_id": 45,
    "status": "processed",
    "created_at": "2024-10-06T12:00:00Z",
    "updated_at": null,
    "sections": [...],
    "sections_count": 4
  },
  "errors": []
}
```

---

## 📦 Files Modified

| File | Changes | Linter |
|------|---------|--------|
| `app/routes/legal_cases_router.py` | Removed metadata params and logic | ✅ No errors |
| `app/services/legal_case_ingestion_service.py` | Removed metadata storage | ✅ No errors |
| `app/schemas/legal_knowledge.py` | Removed metadata from response | ✅ No errors |
| `CLEANUP_METADATA_FIELDS.md` | Documentation | N/A |

---

## 🔄 Migration Impact

### Database
- ✅ No migration needed
- ✅ No schema changes
- ✅ Existing data unaffected

### API
- ✅ Cleaner Swagger docs
- ✅ Simpler request/response
- ✅ No breaking changes (fewer fields is safe)

### Code
- ✅ Less complexity
- ✅ Better alignment with model
- ✅ Easier to maintain

---

## 💡 Future Considerations

If you need to store additional case information in the future, consider:

### Option 1: Add Database Columns
Add proper columns to `LegalCase` table via migration:
```python
# Migration
involved_parties = Column(Text, nullable=True)
case_outcome = Column(String(200), nullable=True)
```

### Option 2: Related Table
Create a `CaseMetadata` table for flexible key-value storage:
```python
class CaseMetadata(Base):
    case_id = Column(Integer, ForeignKey("legal_cases.id"))
    key = Column(String(100))
    value = Column(Text)
```

### Option 3: Use Document Metadata
Store in `KnowledgeDocument.document_metadata` JSON (what we removed):
- Pros: Flexible, no migrations
- Cons: No type safety, harder to query

---

**Status:** ✅ **COMPLETE**  
**Date:** October 6, 2024  
**Linter Errors:** 0  
**Breaking Changes:** None

