# 📊 Document Upload & Processing Workflow

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    📤 PHASE 1: UPLOAD (Status: raw)                 │
└─────────────────────────────────────────────────────────────────────┘

User uploads file
    │
    ├─→ JSON law/case
    ├─→ PDF document
    ├─→ DOCX document
    └─→ TXT file
         │
         ▼
┌─────────────────────────────────────┐
│  Parse & Store in SQL Database      │
│  - Create KnowledgeDocument         │
│  - Create LawSource/LegalCase       │
│  - Create Articles & Chunks         │
│  - NO Chroma embeddings yet         │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Set Status = "raw"                 │
│  ✅ Content in SQL                  │
│  ❌ NO embeddings in Chroma         │
│  ❌ NOT searchable via RAG          │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  API Response:                      │
│  {                                  │
│    "status": "raw",                 │
│    "next_step": "Call /generate-    │
│                 embeddings"         │
│  }                                  │
└─────────────────────────────────────┘
         │
         │
         │
┌─────────────────────────────────────────────────────────────────────┐
│            🤖 PHASE 2: EMBEDDING GENERATION (Background)            │
└─────────────────────────────────────────────────────────────────────┘

Frontend displays law list
    │
    ▼
┌─────────────────────────────────────┐
│  Law Table Row:                     │
│  ┌────────────────────────────────┐ │
│  │ نظام العمل │ قانون │ [⚠️ غير   │ │
│  │             │       │   معالج]  │ │ ← User clicks status
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Frontend (Optimistic Update)      │
│  1. Update UI immediately           │
│  2. Show "جاري المعالجة" (blue)    │
│  3. Call POST /generate-embeddings  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Backend: Update Status             │
│  1. law_source.status = 'processing'│
│  2. Generate embeddings (AraBERT)   │
│  3. Insert into Chroma vectorstore  │
│  4. law_source.status = 'processed' │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Set Status = "processed"           │
│  ✅ Content in SQL                  │
│  ✅ Embeddings in Chroma            │
│  ✅ Searchable via RAG              │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Frontend (after refresh/poll):     │
│  ┌────────────────────────────────┐ │
│  │ نظام العمل │ قانون │ [✅ معالج] │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 🎨 Status Colors & UI

### Status Badge Design

```
╔════════════════════════════════════════════════════════════════╗
║  STATUS: raw                                                   ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║   ┌──────────────────────────────────────┐                    ║
║   │  ⚠️  غير معالج  (انقر للمعالجة)     │  ← Yellow badge   ║
║   └──────────────────────────────────────┘                    ║
║                                                                ║
║   • Clickable button/badge                                    ║
║   • Hover: pointer cursor                                     ║
║   • Tooltip: "انقر لبدء المعالجة"                             ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════╗
║  STATUS: processing                                            ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║   ┌──────────────────────────────────────┐                    ║
║   │  ⏳  جاري المعالجة...  🔄           │  ← Blue badge     ║
║   └──────────────────────────────────────┘                    ║
║                                                                ║
║   • Disabled (not clickable)                                  ║
║   • Loading spinner animation                                 ║
║   • Tooltip: "يتم المعالجة في الخلفية"                        ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════════╗
║  STATUS: processed                                             ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║   ┌──────────────────────────────────────┐                    ║
║   │  ✅  معالج                           │  ← Green badge    ║
║   └──────────────────────────────────────┘                    ║
║                                                                ║
║   • Disabled (not clickable)                                  ║
║   • Tooltip: "جاهز للاستخدام"                                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

## 🔀 Status Transitions

```
        ┌─────┐
        │ raw │  ← All documents start here
        └──┬──┘
           │
           │  User clicks OR API call
           │  POST /generate-embeddings
           ▼
    ┌────────────┐
    │ processing │  ← Embeddings being generated
    └──────┬─────┘
           │
           │  Embeddings successfully created
           │  in Chroma vectorstore
           ▼
    ┌───────────┐
    │ processed │  ← Ready for RAG queries
    └─────┬─────┘
          │
          │  Optional: AI analysis
          │  POST /analyze-law-with-ai
          ▼
    ┌─────────┐
    │ indexed │  ← AI insights added
    └─────────┘
```

## 📋 API Endpoints

### 1. Upload Document
```http
POST /api/v1/laws/upload
Content-Type: multipart/form-data

{
  "file": <file>,
  "law_name": "نظام العمل السعودي",
  ...
}
```
**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": 123,
    "status": "raw",
    "chunks_created": 245,
    "next_step": "Call POST /api/v1/laws/123/generate-embeddings"
  }
}
```

### 2. List Laws (with status filter)
```http
GET /api/v1/laws?status=raw&page=1&page_size=20
```
**Response:**
```json
{
  "success": true,
  "data": {
    "laws": [
      {
        "id": 1,
        "name": "نظام العمل",
        "status": "raw",
        "knowledge_document_id": 123  ← Use this for generate-embeddings
      }
    ]
  }
}
```

### 3. Generate Embeddings
```http
POST /api/v1/laws/123/generate-embeddings
```
**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": 123,
    "status": "processing",
    "message": "Embeddings are being generated in background"
  }
}
```

### 4. Query RAG (only works with processed documents)
```http
POST /api/v1/laws/query?query=ماهي مهام مفتشي العمل
```
**Response:**
```json
{
  "success": true,
  "data": {
    "answer": "بناءً على المادة 138...",
    "query": "ماهي مهام مفتشي العمل"
  }
}
```

## 🎯 Key Points

1. **Two-Step Process:** Upload → Generate Embeddings
2. **User Control:** User decides when to generate embeddings
3. **Clear Visibility:** Status badge shows exact state
4. **Optimistic UI:** Frontend updates immediately on click
5. **Background Processing:** Embeddings generation doesn't block UI
6. **Data Integrity:** Content preserved even if embeddings fail

## 🚀 Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Upload Speed** | Slow (waits for embeddings) | Fast (SQL only) |
| **Visibility** | Unclear status | Clear status badges |
| **User Control** | Automatic | Manual trigger |
| **Error Handling** | Lost data on failure | Data preserved in SQL |
| **Batch Upload** | Blocking | Non-blocking |
| **Status Accuracy** | "Processed" without embeddings | "Raw" until embeddings done |

---

**Created:** October 28, 2025  
**Status:** ✅ Implemented and tested

