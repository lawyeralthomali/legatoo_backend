# Legal Case Model Update - Document Linking

## ✅ Changes Applied

Successfully updated the `LegalCase` model to include document linking capability.

---

## 📝 What Was Changed

### 1. **LegalCase Model** (`app/models/legal_knowledge.py`)

#### Added Field
```python
document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
```

**Purpose**: Links a legal case to its source document in the `KnowledgeDocument` table.

#### Added Relationship
```python
document = relationship("KnowledgeDocument", foreign_keys=[document_id])
```

**Purpose**: Enables easy access to the source document from a legal case instance.

---

### 2. **Updated Indexes**

#### Modified Index
```python
# Before:
Index('idx_knowledge_chunks_hierarchy', 
    KnowledgeChunk.law_source_id, 
    KnowledgeChunk.branch_id, 
    KnowledgeChunk.chapter_id, 
    KnowledgeChunk.article_id
)

# After:
Index('idx_knowledge_chunks_hierarchy', 
    KnowledgeChunk.law_source_id, 
    KnowledgeChunk.branch_id, 
    KnowledgeChunk.chapter_id, 
    KnowledgeChunk.article_id, 
    KnowledgeChunk.case_id  # ← Added
)
```

**Purpose**: Improves query performance when searching knowledge chunks by legal case.

---

### 3. **Existing Features Confirmed**

✅ **CaseSection Model** - Already exists with all required fields:
- `id`, `case_id`, `section_type`, `content`, `embedding`, `ai_processed_at`, `created_at`
- Relationship: `case = relationship("LegalCase", back_populates="sections")`

✅ **LegalCase Relationships** - Already configured:
- `sections = relationship("CaseSection", back_populates="case", cascade="all, delete-orphan")`
- `chunks = relationship("KnowledgeChunk", back_populates="legal_case")`

✅ **KnowledgeChunk Links** - Already exists:
- `case_id = Column(Integer, ForeignKey("legal_cases.id"), nullable=True)`
- `legal_case = relationship("LegalCase", back_populates="chunks")`

---

## 🗄️ Database Migration

### Migration File Created
**File**: `alembic/versions/007_add_document_id_to_legal_cases.py`

### To Apply Migration

```bash
# Run the migration
alembic upgrade head
```

### What the Migration Does

1. **Adds** `document_id` column to `legal_cases` table
2. **Creates** foreign key constraint to `knowledge_documents.id`
3. **Creates** index on `document_id` for performance
4. **Updates** `idx_knowledge_chunks_hierarchy` index to include `case_id`

### Rollback (if needed)

```bash
# Rollback to previous version
alembic downgrade -1
```

---

## 📊 Updated Schema Diagram

```
KnowledgeDocument
    ↓ (1-to-many)
LegalCase
    ↓ (1-to-many)
    ├─→ CaseSection (summary, facts, arguments, ruling, legal_basis)
    └─→ KnowledgeChunk (text chunks for semantic search)
```

---

## 🔗 Relationships Overview

### LegalCase → KnowledgeDocument
```python
# Access document from case
case = session.query(LegalCase).get(1)
document = case.document

# Access cases from document (via backref)
document = session.query(KnowledgeDocument).get(1)
# Note: No direct backref, need to query LegalCase with filter
cases = session.query(LegalCase).filter_by(document_id=document.id).all()
```

### LegalCase → CaseSection
```python
# Access sections from case
case = session.query(LegalCase).get(1)
sections = case.sections

# Access case from section
section = session.query(CaseSection).get(1)
case = section.case
```

### LegalCase → KnowledgeChunk
```python
# Access chunks from case
case = session.query(LegalCase).get(1)
chunks = case.chunks

# Access case from chunk
chunk = session.query(KnowledgeChunk).get(1)
case = chunk.legal_case
```

---

## 💡 Usage Examples

### Example 1: Create Legal Case with Document Link

```python
from app.models.legal_knowledge import LegalCase, KnowledgeDocument, CaseSection
from datetime import date

# Create or get knowledge document
document = KnowledgeDocument(
    title="قضية رقم 123/2024",
    category="case",
    file_path="/uploads/case_123.pdf",
    source_type="uploaded",
    status="raw"
)
session.add(document)
session.flush()  # Get document.id

# Create legal case linked to document
legal_case = LegalCase(
    case_number="123/2024",
    title="قضية عمالية - فصل تعسفي",
    jurisdiction="الرياض",
    court_name="محكمة العمل",
    decision_date=date(2024, 10, 5),
    case_type="عمل",
    court_level="ابتدائي",
    document_id=document.id,  # ← Link to document
    status="raw"
)
session.add(legal_case)
session.flush()

# Add case sections
sections_data = [
    ("summary", "ملخص القضية..."),
    ("facts", "وقائع القضية..."),
    ("arguments", "حجج الأطراف..."),
    ("ruling", "منطوق الحكم..."),
    ("legal_basis", "الأساس القانوني...")
]

for section_type, content in sections_data:
    section = CaseSection(
        case_id=legal_case.id,
        section_type=section_type,
        content=content
    )
    session.add(section)

session.commit()
```

---

### Example 2: Query Cases by Document

```python
# Find all cases linked to a specific document
document_id = 1
cases = session.query(LegalCase).filter_by(document_id=document_id).all()

for case in cases:
    print(f"Case: {case.case_number} - {case.title}")
    print(f"Document: {case.document.title if case.document else 'N/A'}")
```

---

### Example 3: Update Existing Case to Link Document

```python
# Link an existing case to a document
case = session.query(LegalCase).filter_by(case_number="123/2024").first()
document = session.query(KnowledgeDocument).filter_by(
    file_path="/uploads/case_123.pdf"
).first()

if case and document:
    case.document_id = document.id
    session.commit()
    print(f"Linked case {case.case_number} to document {document.title}")
```

---

### Example 4: Access All Related Data

```python
# Complete case data with all relationships
case = session.query(LegalCase).options(
    joinedload(LegalCase.document),
    joinedload(LegalCase.sections),
    joinedload(LegalCase.chunks)
).filter_by(id=1).first()

print(f"Case: {case.title}")
print(f"Document: {case.document.title if case.document else 'No document'}")
print(f"Sections: {len(case.sections)}")
print(f"Chunks: {len(case.chunks)}")

# Print sections
for section in case.sections:
    print(f"  - {section.section_type}: {section.content[:50]}...")
```

---

## 🔍 Benefits of This Update

### 1. **Document Traceability**
- Each legal case can now be linked to its source PDF/document
- Easy to find which document a case came from
- Supports audit trail and compliance requirements

### 2. **Improved Data Integrity**
- `ondelete="SET NULL"` ensures cases aren't deleted when document is removed
- Maintains referential integrity in the database
- Cascading deletes properly handle sections and chunks

### 3. **Better Query Performance**
- Indexed `document_id` field allows fast lookups
- Updated hierarchy index improves knowledge chunk queries
- Efficient joins between cases and documents

### 4. **Flexible Data Model**
- `nullable=True` allows cases without documents (legacy data)
- Can link multiple cases to same document (e.g., appeal cases)
- Supports both uploaded and scraped cases

---

## ⚠️ Important Notes

### Backward Compatibility
✅ **Fully backward compatible**
- Existing cases will have `document_id = NULL`
- All existing relationships remain intact
- No data loss during migration

### Data Migration Strategy
If you have existing cases and want to link them to documents:

```python
# Script to link existing cases to documents
from app.models.legal_knowledge import LegalCase, KnowledgeDocument
from app.db.database import get_db

async def link_cases_to_documents():
    db = get_db()
    
    # Find cases without documents
    cases = db.query(LegalCase).filter(LegalCase.document_id.is_(None)).all()
    
    for case in cases:
        # Try to find matching document by case number or title
        document = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.title.contains(case.case_number)
        ).first()
        
        if document:
            case.document_id = document.id
            print(f"Linked case {case.id} to document {document.id}")
    
    db.commit()
    print(f"Linked {len(cases)} cases to documents")
```

### Performance Considerations
- The new index adds minimal storage overhead
- Query performance improves for document-based searches
- Consider adding index on `(document_id, decision_date)` if frequently querying by both

---

## 📚 Related Files

| File | Status | Purpose |
|------|--------|---------|
| `app/models/legal_knowledge.py` | ✅ Updated | Model definitions |
| `alembic/versions/007_add_document_id_to_legal_cases.py` | ✅ Created | Database migration |
| `LEGAL_CASE_MODEL_UPDATE.md` | ✅ Created | This documentation |

---

## ✅ Checklist

- [x] Added `document_id` field to `LegalCase` model
- [x] Added `document` relationship to `LegalCase`
- [x] Updated `idx_knowledge_chunks_hierarchy` index
- [x] Confirmed `CaseSection` model exists with all required fields
- [x] Confirmed `KnowledgeChunk` has `case_id` and relationship
- [x] Created Alembic migration script
- [x] No linting errors
- [x] Backward compatible
- [x] Documentation complete

---

## 🚀 Next Steps

1. **Run the migration**:
   ```bash
   alembic upgrade head
   ```

2. **Test the changes**:
   ```bash
   # Start your server
   uvicorn app.main:app --reload
   
   # Or
   py run.py
   ```

3. **Update your API/services** to use the new `document_id` field when creating legal cases

4. **Optional**: Run the data migration script to link existing cases to documents

---

**Status**: ✅ **COMPLETE**  
**Date**: October 6, 2025  
**Version**: 007  
**Breaking Changes**: None (fully backward compatible)
