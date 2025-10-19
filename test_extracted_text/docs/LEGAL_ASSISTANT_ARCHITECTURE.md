# Legal AI Assistant - System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                              │
│                    (Web, Mobile, API Clients)                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ HTTPS / JWT
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                        API GATEWAY LAYER                            │
│                         FastAPI Router                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  legal_assistant_router.py                                   │  │
│  │  - 11 RESTful endpoints                                      │  │
│  │  - Request validation (Pydantic)                             │  │
│  │  - Authentication & Authorization                            │  │
│  │  - Unified response format                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ Service calls
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                       SERVICE LAYER                                 │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │           LegalAssistantService (Orchestrator)                │ │
│  │  - Coordinates all document operations                        │ │
│  │  - Manages processing pipeline                                │ │
│  │  - Handles search orchestration                               │ │
│  └───────────┬────────────────┬────────────────┬─────────────────┘ │
│              │                │                │                    │
│  ┌───────────▼───────┐  ┌────▼─────────┐  ┌──▼──────────────────┐ │
│  │ Document          │  │  Embedding   │  │  Semantic Search    │ │
│  │ Processing        │  │  Service     │  │  Service            │ │
│  │ Service           │  │              │  │                     │ │
│  │                   │  │  - OpenAI    │  │  - Vector search    │ │
│  │ - PDF/DOCX/TXT    │  │    API       │  │  - Keyword filter   │ │
│  │ - Text extraction │  │  - 3072-dim  │  │  - Similarity calc  │ │
│  │ - Chunking        │  │  - Batch     │  │  - Ranking          │ │
│  │ - Entity detect   │  │    process   │  │  - Highlighting     │ │
│  └───────────────────┘  └──────────────┘  └─────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ Repository calls
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                     REPOSITORY LAYER                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  LegalDocumentRepository                                     │  │
│  │  - CRUD operations                                           │  │
│  │  - Query building                                            │  │
│  │  - Filtering & pagination                                    │  │
│  │  - Chunk management                                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ ORM (SQLAlchemy)
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                       DATABASE LAYER                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  SQLite (Dev) / PostgreSQL (Prod)                           │  │
│  │                                                              │  │
│  │  Tables:                                                     │  │
│  │  - legal_documents                                           │  │
│  │  - legal_document_chunks                                     │  │
│  │  - profiles (FK)                                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                      EXTERNAL SERVICES                              │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  OpenAI API     │  │  File System     │  │  Email Service   │  │
│  │  (Embeddings)   │  │  (Document       │  │  (Notifications) │  │
│  │                 │  │   Storage)       │  │                  │  │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📂 File Structure

```
app/
├── routes/
│   └── legal_assistant_router.py      # 11 API endpoints
│
├── services/
│   ├── legal_assistant_service.py     # Main orchestrator
│   ├── document_processing_service.py # Text extraction & chunking
│   ├── embedding_service.py           # OpenAI embeddings
│   └── semantic_search_service.py     # Search & ranking
│
├── repositories/
│   └── legal_document_repository.py   # Data access layer
│
├── models/
│   └── legal_document2.py             # SQLAlchemy models
│
├── schemas/
│   └── legal_assistant.py             # Pydantic validation
│
└── db/
    └── database.py                    # Database connection

uploads/
└── legal_documents/                   # Uploaded files
    └── {uuid}.pdf

docs/
├── LEGAL_ASSISTANT_COMPLETE_GUIDE.md  # This document!
├── LEGAL_ASSISTANT_QUICK_REFERENCE.md # Quick reference
├── LEGAL_ASSISTANT_README.md          # API docs
└── LEGAL_ASSISTANT_IMPLEMENTATION_SUMMARY.md
```

---

## 🔄 Processing Pipeline Flow

```
                    ┌──────────────────┐
                    │  User Uploads    │
                    │  Document        │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Save File       │
                    │  to Disk         │
                    │  (UUID filename) │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Create DB       │
                    │  Record          │
                    │  status: pending │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Background Task │
                    │  (Async)         │
                    └────────┬─────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
   ┌────▼─────┐  ┌─────────┐  ┌─────────┐  ┌────▼──────┐
   │ Extract  │→ │ Chunk   │→ │ Detect  │→ │ Generate  │
   │ Text     │  │ Text    │  │ Entities│  │ Embeddings│
   │ (PyPDF2) │  │(200-500)│  │(Article)│  │ (OpenAI)  │
   └──────────┘  └─────────┘  └─────────┘  └─────┬─────┘
                                                  │
                                         ┌────────▼────────┐
                                         │  Store in DB    │
                                         │  status: done   │
                                         └─────────────────┘
```

---

## 🔍 Search Pipeline Flow

```
                    ┌──────────────────┐
                    │  User Submits    │
                    │  Search Query    │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Generate Query  │
                    │  Embedding       │
                    │  (OpenAI API)    │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Apply Keyword   │
                    │  Filters         │
                    │  (type, lang)    │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Fetch Candidate │
                    │  Chunks          │
                    │  (limit: 1000)   │
                    └────────┬─────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
   ┌────▼─────┐  ┌─────────┐  ┌─────────┐  ┌────▼──────┐
   │Calculate │→ │ Filter  │→ │  Sort   │→ │ Extract   │
   │Similarity│  │ by      │  │  by     │  │Highlights │
   │ (Cosine) │  │Threshold│  │ Score   │  │           │
   └──────────┘  └─────────┘  └─────────┘  └─────┬─────┘
                                                  │
                                         ┌────────▼────────┐
                                         │  Return Results │
                                         │  + Query Time   │
                                         └─────────────────┘
```

---

## 🎯 Service Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    LegalAssistantService                        │
│                                                                 │
│  upload_document()     ┌────────────────────────────────────┐  │
│  ├─ validate           │                                    │  │
│  ├─ save_file          │   Coordinates all operations       │  │
│  └─ create_task ───────┤                                    │  │
│                        │   Delegates to specialized         │  │
│  process_document()    │   services for:                    │  │
│  ├─ extract ────────┐  │   - Document processing           │  │
│  ├─ chunk ──────────┤  │   - Embedding generation          │  │
│  ├─ detect ─────────┤  │   - Semantic search               │  │
│  └─ embed ──────────┤  │                                    │  │
│                     │  │   Manages repository access        │  │
│  search_documents() │  │                                    │  │
│  ├─ embed_query ────┤  └────────────────────────────────────┘  │
│  ├─ filter ─────────┤            │           │           │     │
│  └─ rank ───────────┤            │           │           │     │
│                     │            │           │           │     │
└─────────────────────┼────────────┼───────────┼───────────┼─────┘
                      │            │           │           │
         ┌────────────▼──┐  ┌──────▼──────┐  ┌▼─────────┐ │
         │ Document      │  │  Embedding  │  │ Semantic │ │
         │ Processing    │  │  Service    │  │ Search   │ │
         │ Service       │  │             │  │ Service  │ │
         │               │  │  - OpenAI   │  │          │ │
         │ - PyPDF2      │  │  - Retry    │  │ - Cosine │ │
         │ - python-docx │  │  - Batch    │  │ - Filter │ │
         │ - Chunking    │  │  - Fallback │  │ - Rank   │ │
         │ - Entities    │  │             │  │          │ │
         └───────────────┘  └─────────────┘  └──────────┘ │
                                                           │
                            ┌──────────────────────────────▼──┐
                            │  LegalDocumentRepository        │
                            │  - CRUD operations              │
                            │  - Query building               │
                            └─────────────────────────────────┘
```

---

## 💾 Data Model Relationships

```
┌──────────────────┐
│   profiles       │
│  (User info)     │
└────────┬─────────┘
         │
         │ uploaded_by_id (FK)
         │
         │ 1:N
         │
┌────────▼──────────────────────────────────┐
│   legal_documents                         │
│  ─────────────────────────────────────    │
│  id                  INTEGER PK           │
│  title               VARCHAR(255)         │
│  file_path           VARCHAR(500)         │
│  uploaded_by_id      INTEGER FK           │
│  document_type       VARCHAR(50)          │
│  language            VARCHAR(10)          │
│  is_processed        BOOLEAN              │
│  processing_status   VARCHAR(20)          │
│  created_at          DATETIME             │
│  notes               TEXT                 │
└────────┬──────────────────────────────────┘
         │
         │ document_id (FK)
         │
         │ 1:N
         │
┌────────▼──────────────────────────────────┐
│   legal_document_chunks                   │
│  ─────────────────────────────────────    │
│  id                  INTEGER PK           │
│  document_id         INTEGER FK           │
│  chunk_index         INTEGER              │
│  content             TEXT                 │
│  article_number      VARCHAR(50)          │
│  section_title       VARCHAR(255)         │
│  keywords            JSON [array]         │
│  embedding           JSON [3072 floats]   │
│  created_at          DATETIME             │
└───────────────────────────────────────────┘
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Security Layers                              │
└─────────────────────────────────────────────────────────────────┘

1. Authentication Layer
   ┌──────────────────────────────────────────┐
   │  JWT Token Validation                    │
   │  - Verify signature                      │
   │  - Check expiration                      │
   │  - Extract user ID                       │
   └──────────────────────────────────────────┘

2. Authorization Layer
   ┌──────────────────────────────────────────┐
   │  Role-Based Access Control               │
   │  - Super Admin: Full access              │
   │  - User: Own documents only              │
   └──────────────────────────────────────────┘

3. Input Validation
   ┌──────────────────────────────────────────┐
   │  Pydantic Schema Validation              │
   │  - File type validation                  │
   │  - Size limits                           │
   │  - SQL injection prevention              │
   └──────────────────────────────────────────┘

4. Data Protection
   ┌──────────────────────────────────────────┐
   │  - File system isolation (UUID names)    │
   │  - Database constraints                  │
   │  - Error masking (no stack traces)       │
   └──────────────────────────────────────────┘

5. API Security
   ┌──────────────────────────────────────────┐
   │  - CORS configuration                    │
   │  - Rate limiting (future)                │
   │  - HTTPS only (production)               │
   └──────────────────────────────────────────┘
```

---

## ⚡ Performance Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Performance Optimizations                      │
└─────────────────────────────────────────────────────────────────┘

1. Async Operations
   ┌──────────────────────────────────────────┐
   │  - Non-blocking I/O (asyncio)            │
   │  - Concurrent API calls                  │
   │  - Background task processing            │
   └──────────────────────────────────────────┘

2. Batch Processing
   ┌──────────────────────────────────────────┐
   │  - 50 chunks per embedding batch         │
   │  - Concurrent embedding generation       │
   │  - Bulk database inserts                 │
   └──────────────────────────────────────────┘

3. Database Indexing
   ┌──────────────────────────────────────────┐
   │  - Primary keys                          │
   │  - Foreign keys                          │
   │  - document_type, language, status       │
   └──────────────────────────────────────────┘

4. Search Optimization
   ┌──────────────────────────────────────────┐
   │  - Pre-filtering (keyword filters)       │
   │  - Limit candidate chunks (1000 max)     │
   │  - Early threshold filtering             │
   │  - Top-K selection                       │
   └──────────────────────────────────────────┘

5. Caching Strategy (Future)
   ┌──────────────────────────────────────────┐
   │  - Query result caching (Redis)          │
   │  - Embedding caching                     │
   │  - Document metadata caching             │
   └──────────────────────────────────────────┘
```

---

## 🌊 Request/Response Flow

### Upload Request Flow
```
Client
  │
  ├─ POST /documents/upload (multipart/form-data)
  │   ├─ file: binary
  │   ├─ title: string
  │   ├─ document_type: enum
  │   └─ language: enum
  │
  ▼
Router (legal_assistant_router.py)
  │
  ├─ Validate file extension
  ├─ Save to disk (UUID)
  │
  ▼
Service (LegalAssistantService)
  │
  ├─ upload_document()
  │   ├─ Validate format
  │   ├─ Create DB record
  │   └─ Trigger background task
  │
  ▼
Repository (LegalDocumentRepository)
  │
  ├─ create_document()
  │   └─ INSERT INTO legal_documents
  │
  ▼
Database (SQLite/PostgreSQL)
  │
  ├─ Save record
  │
  ▼
Background Task (asyncio)
  │
  ├─ process_document()
  │   ├─ Extract text
  │   ├─ Chunk text
  │   ├─ Detect entities
  │   ├─ Generate embeddings
  │   └─ Update chunks
  │
  ▼
Response to Client
  │
  └─ { "success": true, "data": {...} }
```

### Search Request Flow
```
Client
  │
  ├─ POST /documents/search
  │   ├─ query: string
  │   ├─ filters: object
  │   └─ limit: int
  │
  ▼
Router (legal_assistant_router.py)
  │
  ├─ Validate SearchRequest schema
  │
  ▼
Service (LegalAssistantService)
  │
  ├─ search_documents()
  │   ├─ Generate query embedding
  │   ├─ Apply filters
  │   ├─ Calculate similarities
  │   ├─ Sort and rank
  │   └─ Enrich with metadata
  │
  ▼
OpenAI API (External)
  │
  ├─ Generate embedding [3072]
  │
  ▼
Repository (LegalDocumentRepository)
  │
  ├─ search_chunks_by_filters()
  │   └─ SELECT chunks WHERE ...
  │
  ▼
Database (SQLite/PostgreSQL)
  │
  ├─ Return candidate chunks
  │
  ▼
Similarity Calculation (In-Memory)
  │
  ├─ Cosine similarity for each chunk
  ├─ Filter by threshold
  └─ Sort DESC
  │
  ▼
Response to Client
  │
  └─ {
        "results": [...],
        "query_time_ms": 42.3
      }
```

---

## 🧩 Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                       Technology Stack                          │
└─────────────────────────────────────────────────────────────────┘

Backend Framework
  ├─ FastAPI (async web framework)
  ├─ Uvicorn (ASGI server)
  └─ Python 3.10+

Database
  ├─ SQLAlchemy (ORM)
  ├─ SQLite (development)
  └─ PostgreSQL (production)

Document Processing
  ├─ PyPDF2 (PDF extraction)
  ├─ python-docx (DOCX extraction)
  └─ regex (pattern matching)

AI/ML
  ├─ OpenAI API (text-embedding-3-large)
  ├─ numpy (vector operations)
  └─ httpx (async HTTP client)

Validation
  ├─ Pydantic (schema validation)
  └─ FastAPI validators

Authentication
  ├─ JWT (JSON Web Tokens)
  └─ bcrypt (password hashing)

Utilities
  ├─ asyncio (async operations)
  ├─ logging (error tracking)
  └─ pathlib (file handling)
```

---

## 📈 Scalability Considerations

### Current Architecture (Single Server)
```
┌────────────────────┐
│   FastAPI Server   │
│   ┌─────────────┐  │
│   │  Service    │  │
│   │  Layer      │  │
│   └──────┬──────┘  │
│          │         │
│   ┌──────▼──────┐  │
│   │  Database   │  │
│   │  (SQLite)   │  │
│   └─────────────┘  │
└────────────────────┘
```

### Future Scaling (Distributed)
```
┌─────────────────────────────────────────────────────────────────┐
│                       Load Balancer                             │
└──────┬────────────────────┬─────────────────────┬───────────────┘
       │                    │                     │
┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
│  API Server │      │  API Server │      │  API Server │
│     #1      │      │     #2      │      │     #3      │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                     │
       └────────────────────┴─────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
       ┌──────▼──────┐           ┌────────▼────────┐
       │  PostgreSQL │           │  Vector DB      │
       │  (Primary)  │           │  (Pinecone/     │
       │             │           │   Weaviate)     │
       └─────────────┘           └─────────────────┘
```

---

## 🎯 Future Enhancements

1. **Vector Database Integration**
   - Pinecone / Weaviate for production scale
   - Faster similarity search (ANN algorithms)

2. **Caching Layer**
   - Redis for query result caching
   - Reduce OpenAI API calls

3. **Message Queue**
   - RabbitMQ / Celery for background tasks
   - Better job management

4. **Monitoring & Analytics**
   - Prometheus metrics
   - Grafana dashboards
   - Query analytics

5. **Advanced Features**
   - Multi-modal search (text + metadata)
   - Document comparison
   - Auto-summarization
   - Q&A chatbot

---

**Last Updated**: October 1, 2025

