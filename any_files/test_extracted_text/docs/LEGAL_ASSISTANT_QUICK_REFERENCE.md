# Legal AI Assistant - Quick Reference

## 🚀 Quick Start

### 1. Upload a Document
```bash
POST /api/v1/legal-assistant/documents/upload
```
```json
{
  "file": "document.pdf",
  "title": "Contract Name",
  "document_type": "employment_contract",
  "language": "ar"
}
```

### 2. Search Documents
```bash
POST /api/v1/legal-assistant/documents/search
```
```json
{
  "query": "employee rights vacation",
  "language": "ar",
  "limit": 10
}
```

---

## 📡 All Endpoints at a Glance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents/upload` | POST | Upload new document |
| `/documents/search` | POST | Semantic search |
| `/documents` | GET | List all documents |
| `/documents/{id}` | GET | Get single document |
| `/documents/{id}` | PUT | Update document |
| `/documents/{id}` | DELETE | Delete document |
| `/documents/{id}/chunks` | GET | Get document chunks |
| `/documents/{id}/progress` | GET | Check processing status |
| `/documents/{id}/reprocess` | POST | Reprocess document |
| `/chunks/{id}` | GET | Get single chunk |
| `/statistics` | GET | System statistics |

---

## 🔄 Complete Workflow

```
Upload → Extract → Chunk → Detect Entities → Generate Embeddings → Search
  ↓         ↓        ↓            ↓                    ↓              ↓
 File    PyPDF2   200-500   Article/Section      OpenAI API    Similarity
 Save     Text     words      Detection           3072-dim      Ranking
```

---

## 📊 Data Models

### Document
```json
{
  "id": 1,
  "title": "Labor Law",
  "document_type": "labor_law",
  "language": "ar",
  "processing_status": "done",
  "is_processed": true,
  "chunks_count": 142
}
```

### Chunk
```json
{
  "id": 45,
  "chunk_index": 12,
  "content": "المادة 109...",
  "article_number": "109",
  "section_title": "الباب السادس",
  "keywords": ["إجازة", "سنوية"],
  "embedding": [0.123, ...],  // 3072 floats
  "similarity_score": 0.92
}
```

### Search Result
```json
{
  "results": [
    {
      "chunk": { /* chunk data */ },
      "document": { /* document data */ },
      "similarity_score": 0.92,
      "highlights": ["matching phrases"]
    }
  ],
  "total_found": 5,
  "query_time_ms": 42.3
}
```

---

## 🎯 Document Types

- `employment_contract` - Employment contracts
- `partnership_contract` - Partnership agreements
- `service_contract` - Service contracts
- `lease_contract` - Lease agreements
- `sales_contract` - Sales contracts
- `labor_law` - Labor laws
- `commercial_law` - Commercial laws
- `civil_law` - Civil laws
- `other` - Other documents

---

## 🌍 Supported Languages

- `ar` - Arabic (with RTL support)
- `en` - English
- `fr` - French

---

## ⚡ Performance Targets

| Operation | Target Time |
|-----------|-------------|
| Upload API | < 1 second |
| Processing (10 pages) | ~15 seconds |
| Search query | < 100ms |
| Embedding generation | ~600ms/chunk |

---

## 🔑 Key Features

### Intelligent Chunking
- ✅ 200-500 words per chunk
- ✅ Maintains sentence boundaries
- ✅ 50-word overlap between chunks
- ✅ Preserves legal context

### Legal Entity Detection
- ✅ Article numbers (Arabic: المادة ١٠٩)
- ✅ Sections (Arabic: الباب السادس)
- ✅ Clauses and references
- ✅ Keyword extraction

### Semantic Search
- ✅ Vector similarity (cosine)
- ✅ Keyword filtering
- ✅ Multi-language support
- ✅ Highlighted results

---

## 🔐 Authentication

All endpoints require JWT:
```http
Authorization: Bearer <your_access_token>
```

Get token from:
```bash
POST /api/v1/auth/login
```

---

## 📝 Example Queries

### Arabic
```
"ما هي حقوق العامل في الإجازات السنوية؟"
"شروط إنهاء العقد"
"مكافأة نهاية الخدمة"
```

### English
```
"What are employee vacation rights?"
"Contract termination conditions"
"End of service gratuity"
```

---

## 🛠️ Environment Setup

```bash
# Required
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///./app.db

# Optional
EMBEDDING_MODEL=text-embedding-3-large
UPLOAD_DIR=uploads/legal_documents
CHUNK_MIN_SIZE=200
CHUNK_MAX_SIZE=500
```

---

## 📚 Processing Statuses

| Status | Description |
|--------|-------------|
| `pending` | Not started |
| `processing` | In progress |
| `done` | Completed successfully |
| `error` | Processing failed |

---

## ✅ Response Format

All endpoints return:
```json
{
  "success": true/false,
  "message": "Human-readable message",
  "data": { /* response data */ },
  "errors": [ /* error details */ ]
}
```

---

## 🎓 Architecture Layers

```
Routes → Services → Repositories → Database
  ↓         ↓            ↓             ↓
 HTTP    Business      Data         SQLite/
Handling  Logic       Access       PostgreSQL
```

---

**Quick Links**:
- [Complete Guide](./LEGAL_ASSISTANT_COMPLETE_GUIDE.md)
- [API Documentation](./LEGAL_ASSISTANT_README.md)
- [Implementation Details](./LEGAL_ASSISTANT_IMPLEMENTATION_SUMMARY.md)

