# Legal Knowledge Management Schema Update

## Overview
This document describes the database schema modifications applied to the legal knowledge management system to improve document tracking, AI processing monitoring, and prevent duplicate uploads.

**Migration Version:** `006_update_legal_knowledge_schema`  
**Date:** October 5, 2025

---

## Summary of Changes

### 🎯 Main Goals
1. **Unified Document References** - Centralize file references through `KnowledgeDocument`
2. **Processing Status Tracking** - Track processing states for laws and cases
3. **AI Processing Audit** - Record when AI processes content
4. **Duplicate Prevention** - Use file hashing to prevent duplicate uploads
5. **Admin Verification** - Allow manual verification of chunks

---

## Detailed Changes by Model

### 1. **LawSource** (المصادر القانونية)

#### ✅ Changes Applied:
- **Removed:** `upload_file_path` (deprecated in favor of unified document reference)
- **Added:** `knowledge_document_id` (FK to `KnowledgeDocument`) - Links to source document
- **Added:** `status` (ENUM: 'raw', 'processed', 'indexed') - Tracks processing state

#### Schema:
```python
class LawSource(Base):
    # ... existing fields ...
    knowledge_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), CheckConstraint("status IN ('raw', 'processed', 'indexed')"), default="raw", index=True)
    
    # Relationships
    knowledge_document = relationship("KnowledgeDocument", foreign_keys=[knowledge_document_id])
```

#### Migration Strategy:
- Existing `upload_file_path` values should be migrated to `KnowledgeDocument` entries before dropping
- All existing records will default to `status='raw'`

---

### 2. **LawBranch** (الأبواب القانونية)

#### ✅ Changes Applied:
- **Added:** `source_document_id` (FK to `KnowledgeDocument`) - References original document

#### Schema:
```python
class LawBranch(Base):
    # ... existing fields ...
    source_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    source_document = relationship("KnowledgeDocument", foreign_keys=[source_document_id])
```

#### Use Case:
Tracks which document a branch was extracted from, useful for re-processing and audit trails.

---

### 3. **LawChapter** (الفصول القانونية)

#### ✅ Changes Applied:
- **Added:** `source_document_id` (FK to `KnowledgeDocument`) - References original document

#### Schema:
```python
class LawChapter(Base):
    # ... existing fields ...
    source_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    source_document = relationship("KnowledgeDocument", foreign_keys=[source_document_id])
```

#### Use Case:
Maintains traceability from chapter to source document for verification and updates.

---

### 4. **LawArticle** (المواد القانونية)

#### ✅ Changes Applied:
- **Added:** `ai_processed_at` (DateTime) - Timestamp of last AI processing
- **Added:** `source_document_id` (FK to `KnowledgeDocument`) - References original document

#### Schema:
```python
class LawArticle(Base):
    # ... existing fields ...
    ai_processed_at = Column(DateTime(timezone=True), nullable=True)
    source_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    source_document = relationship("KnowledgeDocument", foreign_keys=[source_document_id])
```

#### Use Case:
- `ai_processed_at`: Tracks when AI last analyzed the article (for embeddings, keywords, etc.)
- `source_document_id`: Links article to its source document

---

### 5. **LegalCase** (القضايا القانونية)

#### ✅ Changes Applied:
- **Added:** `status` (ENUM: 'raw', 'processed', 'indexed') - Tracks processing state

#### Schema:
```python
class LegalCase(Base):
    # ... existing fields ...
    status = Column(String(50), CheckConstraint("status IN ('raw', 'processed', 'indexed')"), default="raw", index=True)
```

#### Status States:
- **raw:** Uploaded but not processed
- **processed:** Text extracted and analyzed
- **indexed:** Embedded and searchable

---

### 6. **CaseSection** (أقسام القضايا)

#### ✅ Changes Applied:
- **Added:** `ai_processed_at` (DateTime) - Timestamp of AI processing per section

#### Schema:
```python
class CaseSection(Base):
    # ... existing fields ...
    ai_processed_at = Column(DateTime(timezone=True), nullable=True)
```

#### Use Case:
Tracks when AI processed each case section (summary, facts, arguments, ruling, legal_basis).

---

### 7. **KnowledgeChunk** (قطع المعرفة)

#### ✅ Changes Applied:
- **Added:** `verified_by_admin` (Boolean, default=False) - Manual verification flag

#### Schema:
```python
class KnowledgeChunk(Base):
    # ... existing fields ...
    verified_by_admin = Column(Boolean, default=False, index=True)
```

#### Use Case:
- Admins can manually verify chunks for accuracy
- Enables filtering for verified vs unverified content
- Quality control for legal content

---

### 8. **KnowledgeDocument** (المستندات المعرفية)

#### ✅ Changes Applied:
- **Added:** `file_hash` (String(64), unique) - SHA-256 hash for duplicate detection

#### Schema:
```python
class KnowledgeDocument(Base):
    # ... existing fields ...
    file_hash = Column(String(64), unique=True, index=True, nullable=True)
```

#### Use Case:
- Calculate SHA-256 hash on upload
- Prevent duplicate file uploads
- Detect if same content uploaded multiple times
- Enable deduplication workflows

#### Implementation Example:
```python
import hashlib

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
```

---

### 9. **AnalysisResult** (نتائج التحليل)

#### ✅ Changes Applied:
- **Added:** `processed_by` (FK to `users.id`) - Tracks who/what performed analysis

#### Schema:
```python
class AnalysisResult(Base):
    # ... existing fields ...
    processed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    processor = relationship("User", foreign_keys=[processed_by])
```

#### Use Case:
- Track which user or system process performed the analysis
- Audit trail for AI processing
- Accountability for analysis results

---

## Database Migration

### Running the Migration

```bash
# Upgrade to new schema
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Pre-Migration Checklist

1. **Backup Database:**
   ```bash
   cp app.db app.db.backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **Migrate Existing Files:**
   - Create `KnowledgeDocument` entries for existing `law_sources` with `upload_file_path`
   - Link `knowledge_document_id` to new records
   - Then apply migration to drop `upload_file_path`

3. **Set Default Status:**
   - All existing `LawSource` and `LegalCase` records will get `status='raw'`
   - Review and update based on actual processing state

---

## API Impact

### 🔄 Endpoints Affected

#### 1. **Law Source Upload**
**Before:**
```python
{
  "name": "قانون العمل",
  "upload_file_path": "uploads/law_123.pdf"
}
```

**After:**
```python
{
  "name": "قانون العمل",
  "knowledge_document_id": 456,  # References KnowledgeDocument
  "status": "raw"
}
```

#### 2. **Document Upload Response**
**Enhanced with:**
```python
{
  "id": 123,
  "title": "Contract.pdf",
  "file_hash": "a3b5c7d9...",  # SHA-256 hash
  "status": "raw"
}
```

#### 3. **Chunk Verification Endpoint** (New)
```python
POST /api/v1/knowledge/chunks/{chunk_id}/verify
Response: {
  "chunk_id": 789,
  "verified_by_admin": true,
  "verified_at": "2025-10-05T12:00:00Z"
}
```

---

## Benefits

### 📈 Improvements

1. **Unified Document Management**
   - Single source of truth for file references
   - Easier file management and cleanup
   - Consistent file handling across models

2. **Better Processing Tracking**
   - Know which documents are processed
   - Track AI processing timestamps
   - Identify stale content needing re-processing

3. **Duplicate Prevention**
   - Prevent wasting storage on duplicate files
   - Faster duplicate detection via hash lookup
   - Better user experience (notify of duplicates)

4. **Quality Control**
   - Admin verification of chunks
   - Audit trail of AI processing
   - Filter by verified content only

5. **Enhanced Audit Trail**
   - Track who processed what
   - Timestamp of processing events
   - Full traceability from source to processed data

---

## Usage Examples

### Example 1: Upload with Duplicate Detection

```python
import hashlib
from app.models.legal_knowledge import KnowledgeDocument

async def upload_document_with_dedup(file_path: str, title: str):
    # Calculate file hash
    file_hash = calculate_file_hash(file_path)
    
    # Check for duplicate
    existing = await db.query(KnowledgeDocument).filter_by(file_hash=file_hash).first()
    if existing:
        raise ValueError(f"Document already exists: {existing.title}")
    
    # Create new document
    doc = KnowledgeDocument(
        title=title,
        file_path=file_path,
        file_hash=file_hash,
        status='raw'
    )
    db.add(doc)
    await db.commit()
    return doc
```

### Example 2: Track AI Processing

```python
from datetime import datetime
from app.models.legal_knowledge import LawArticle

async def process_article_with_ai(article_id: int):
    article = await db.query(LawArticle).filter_by(id=article_id).first()
    
    # Perform AI processing
    embeddings = generate_embeddings(article.content)
    keywords = extract_keywords(article.content)
    
    # Update article
    article.embedding = embeddings
    article.keywords = keywords
    article.ai_processed_at = datetime.utcnow()
    
    await db.commit()
```

### Example 3: Verify Chunk

```python
async def verify_chunk(chunk_id: int, admin_user_id: int):
    chunk = await db.query(KnowledgeChunk).filter_by(id=chunk_id).first()
    
    # Mark as verified
    chunk.verified_by_admin = True
    await db.commit()
    
    # Log verification
    logger.info(f"Chunk {chunk_id} verified by admin {admin_user_id}")
```

### Example 4: Update Law Source Status

```python
async def process_law_source(law_source_id: int):
    source = await db.query(LawSource).filter_by(id=law_source_id).first()
    
    # Mark as processing
    source.status = 'processing'
    await db.commit()
    
    try:
        # Extract and process
        await extract_articles(source)
        await generate_embeddings(source)
        
        # Mark as indexed
        source.status = 'indexed'
    except Exception as e:
        source.status = 'error'
        logger.error(f"Failed to process law source {law_source_id}: {e}")
    
    await db.commit()
```

---

## Testing

### Test Migration

```bash
# Test upgrade
alembic upgrade 006_update_legal_knowledge_schema

# Verify schema
python -c "from app.models.legal_knowledge import *; print('Schema OK')"

# Test downgrade
alembic downgrade -1

# Verify rollback
python -c "from app.models.legal_knowledge import *; print('Rollback OK')"

# Upgrade again
alembic upgrade head
```

### Test Data Integrity

```python
# Test file hash uniqueness
def test_duplicate_prevention():
    doc1 = KnowledgeDocument(title="Test", file_hash="abc123")
    doc2 = KnowledgeDocument(title="Test2", file_hash="abc123")
    
    db.add(doc1)
    db.commit()
    
    db.add(doc2)
    with pytest.raises(IntegrityError):  # Should fail on unique constraint
        db.commit()
```

---

## Backward Compatibility

### ⚠️ Breaking Changes

1. **`law_sources.upload_file_path`** removed
   - **Migration Required:** Move to `KnowledgeDocument` first
   - **Alternative:** Use `knowledge_document.file_path` via relationship

### ✅ Non-Breaking Changes

All new columns are nullable with sensible defaults:
- `status` defaults to `'raw'`
- `verified_by_admin` defaults to `False`
- All FK columns are nullable
- All timestamp columns are nullable

---

## Monitoring & Maintenance

### Recommended Indexes (Already Created)

```sql
-- Query optimization
CREATE INDEX idx_law_sources_status ON law_sources(status);
CREATE INDEX idx_legal_cases_status ON legal_cases(status);
CREATE INDEX idx_knowledge_chunks_verified ON knowledge_chunks(verified_by_admin);
CREATE INDEX idx_knowledge_documents_file_hash ON knowledge_documents(file_hash);
```

### Monitoring Queries

```sql
-- Check processing status distribution
SELECT status, COUNT(*) FROM law_sources GROUP BY status;
SELECT status, COUNT(*) FROM legal_cases GROUP BY status;

-- Find unprocessed content
SELECT id, name FROM law_sources WHERE status = 'raw';

-- Find unverified chunks
SELECT id, content FROM knowledge_chunks WHERE verified_by_admin = false;

-- Detect duplicate files
SELECT file_hash, COUNT(*) FROM knowledge_documents 
WHERE file_hash IS NOT NULL 
GROUP BY file_hash HAVING COUNT(*) > 1;
```

---

## Next Steps

1. **Apply Migration:**
   ```bash
   alembic upgrade head
   ```

2. **Update Application Code:**
   - Replace `law_source.upload_file_path` with `law_source.knowledge_document.file_path`
   - Implement file hash calculation on upload
   - Add duplicate detection logic
   - Update status tracking in processing workflows

3. **Create Admin Endpoints:**
   - Chunk verification endpoint
   - Status management endpoint
   - Processing audit logs

4. **Documentation:**
   - Update API documentation
   - Update developer guide
   - Create admin user guide

---

## Support

For questions or issues related to this migration:
- Check migration logs: `logs/alembic.log`
- Review model definitions: `app/models/legal_knowledge.py`
- See examples: This document (usage examples section)

**Migration Created By:** AI Assistant  
**Date:** October 5, 2025  
**Version:** 006_update_legal_knowledge_schema
