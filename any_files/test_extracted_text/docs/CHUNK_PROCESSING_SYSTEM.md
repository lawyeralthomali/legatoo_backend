# 📚 Chunk Processing System - Complete Documentation

## 🎯 Overview

The Chunk Processing System is an AI-powered service that intelligently splits legal documents into semantically meaningful chunks using Google Gemini AI. This system transforms raw document chunks into smaller, legally meaningful segments for better search, analysis, and retrieval.

---

## 🏗️ Architecture

```
┌─────────────────┐
│   API Router    │  ← Handles HTTP requests
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Service      │  ← Business logic & orchestration
└────────┬────────┘
         │
         ├──────────────┐
         ▼              ▼
┌──────────────┐  ┌──────────────┐
│ Repositories │  │  Gemini AI   │  ← Data access & AI processing
└──────────────┘  └──────────────┘
         │
         ▼
┌─────────────────┐
│    Database     │  ← SQLite storage
└─────────────────┘
```

---

## 📁 File Structure

```
app/
├── routes/
│   └── chunk_processing_router.py     ← API endpoints
├── services/
│   └── chunk_processing_service.py    ← Business logic & AI integration
├── repositories/
│   └── legal_knowledge_repository.py  ← Database operations
└── models/
    └── legal_knowledge.py             ← Database models
```

---

## 🔌 API Endpoints

### Base URL: `/api/v1/chunks`

### 1. **POST `/documents/{document_id}/process`**
Process all chunks in a document and convert them to smart chunks.

**Authentication:** Required (Bearer Token)

**Request:**
```http
POST /api/v1/chunks/documents/123/process
Authorization: Bearer <your_token>
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Processed 10 chunks into 45 smart chunks",
  "data": {
    "document_id": 123,
    "document_title": "قانون العمل السعودي",
    "original_chunks_count": 10,
    "new_smart_chunks_count": 45,
    "processing_details": [
      {
        "original_chunk_id": 1,
        "original_content_preview": "المادة الأولى: يسري هذا النظام...",
        "smart_sentences_count": 5,
        "new_chunks_count": 4,
        "processing_method": "gemini_ai"
      }
    ]
  },
  "errors": []
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "Document with ID 123 not found",
  "data": null,
  "errors": [
    {
      "field": "document_id",
      "message": "Document not found"
    }
  ]
}
```

---

### 2. **GET `/documents/{document_id}/status`**
Get the processing status and statistics for a document.

**Authentication:** Required (Bearer Token)

**Request:**
```http
GET /api/v1/chunks/documents/123/status
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Processing status retrieved successfully",
  "data": {
    "document_id": 123,
    "document_title": "قانون العمل السعودي",
    "total_chunks": 45,
    "chunks_with_embeddings": 30,
    "processing_progress": "66.7%",
    "status": "processed"
  },
  "errors": []
}
```

---

### 3. **POST `/documents/{document_id}/generate-embeddings`**
Generate vector embeddings for all chunks (placeholder for future implementation).

**Authentication:** Required (Bearer Token)

**Request:**
```http
POST /api/v1/chunks/documents/123/generate-embeddings
Authorization: Bearer <your_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Embedding generation endpoint - to be implemented",
  "data": {
    "document_id": 123
  },
  "errors": []
}
```

---

## 🔄 Processing Workflow

### Step-by-Step Flow

```
1. User Request
   ↓
2. Authentication Check (JWT Token)
   ↓
3. Document Validation
   ↓
4. Fetch Original Chunks
   ↓
5. For Each Chunk:
   ├── Send to Gemini AI
   ├── Split into Smart Sentences
   ├── Filter Legally Meaningful
   └── Create New Chunks
   ↓
6. Save Smart Chunks (Batch)
   ↓
7. Update Document Status
   ↓
8. Return Results
```

---

## 💻 Code Structure

### 1. Router Layer (`chunk_processing_router.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from ..services.chunk_processing_service import ChunkProcessingService
from ..db.database import get_db
from ..utils.auth import get_current_user
from ..models.user import User
from ..schemas.response import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chunks", tags=["Chunk Processing"])
```

**Key Features:**
- ✅ Unified response structure with `ApiResponse[Dict[str, Any]]`
- ✅ Proper authentication with `get_current_user`
- ✅ Error handling with logging
- ✅ HTTP status codes (400 for validation, 500 for server errors)

---

### 2. Service Layer (`chunk_processing_service.py`)

#### **A. GeminiTextProcessor Class**

Handles AI-powered text splitting using Google Gemini SDK.

```python
class GeminiTextProcessor:
    """Text processor using Google Gemini AI"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self._client = None  # Lazy initialization
    
    async def split_legal_text(self, text: str) -> List[str]:
        """Split legal text using Gemini AI with fallback"""
        # Initialize SDK if needed
        # Call Gemini API with timeout
        # Parse response
        # Return sentences or fallback
```

**Features:**
- 🤖 Uses official Google Gemini SDK (`google.genai`)
- ⏱️ Timeout protection (60 seconds)
- 🔄 Automatic fallback on errors
- 📝 Smart prompt engineering for legal text
- 🧹 Response filtering and cleaning

**Prompt Strategy:**
```
أنت مساعد متخصص في النصوص القانونية العربية
- قسم النص إلى جمل قانونية كاملة
- احتفظ بالمعنى القانوني الكامل
- ركز على الأفعال القانونية (يجب، يجوز، يعاقب)
```

---

#### **B. ChunkProcessingService Class**

Main service orchestrating the entire processing workflow.

```python
class ChunkProcessingService:
    """Service for processing knowledge chunks"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.document_repo = KnowledgeDocumentRepository(db)
        self.chunk_repo = KnowledgeChunkRepository(db)
        self.gemini_processor = GeminiTextProcessor()
```

**Main Methods:**

##### `process_document_chunks(document_id: int)`
```python
async def process_document_chunks(self, document_id: int) -> Dict[str, Any]:
    """
    Main processing method:
    1. Validate document exists
    2. Get original chunks
    3. Process each chunk with AI
    4. Save new smart chunks
    5. Update document status
    6. Return results
    """
```

##### `_process_single_chunk(original_chunk: KnowledgeChunk)`
```python
async def _process_single_chunk(self, original_chunk: KnowledgeChunk):
    """
    Process a single chunk:
    1. Split text with Gemini AI
    2. Filter legally meaningful sentences
    3. Create new chunk objects
    4. Save in batch
    """
```

##### `_is_legally_meaningful(sentence: str)`
```python
def _is_legally_meaningful(self, sentence: str) -> bool:
    """
    Check if sentence has legal value:
    - Length >= 10 characters
    - Contains legal indicators (يجب، يجوز، مادة، قانون)
    - Not just numbers or punctuation
    """
```

##### `_create_smart_chunk(original_chunk, content, index)`
```python
def _create_smart_chunk(self, ...) -> KnowledgeChunk:
    """
    Create new chunk inheriting metadata from original:
    - document_id
    - law_source_id, branch_id, chapter_id, article_id
    - case_id, term_id
    - verified_by_admin = False
    """
```

##### `get_processing_status(document_id: int)`
```python
async def get_processing_status(self, document_id: int):
    """
    Get processing statistics:
    - Total chunks
    - Chunks with embeddings
    - Processing progress percentage
    - Document status
    """
```

---

### 3. Repository Layer (`legal_knowledge_repository.py`)

#### **KnowledgeDocumentRepository**

```python
class KnowledgeDocumentRepository:
    async def get_document_by_id(self, document_id: int)
    async def update_document_status(self, document_id: int, status: str, processed_at: datetime)
```

#### **KnowledgeChunkRepository**

```python
class KnowledgeChunkRepository:
    async def get_chunks_by_document(self, document_id: int, skip: int, limit: int)
    async def save_chunks_batch(self, chunks: List[KnowledgeChunk])
    async def get_chunks_statistics(self, document_id: int)
```

---

## 🗄️ Database Models

### **KnowledgeDocument**

```python
class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    category = Column(String(50))  # 'law', 'case', 'contract', etc.
    file_path = Column(Text)
    status = Column(String(50))  # 'raw', 'processed', 'indexed'
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
    document_metadata = Column(JSON)
```

**Status Values:**
- `raw` - Initial upload
- `processed` - Chunks processed ✅
- `indexed` - Embeddings generated

---

### **KnowledgeChunk**

```python
class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"))
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    tokens_count = Column(Integer)
    embedding = Column(Text)  # JSON-encoded vector
    verified_by_admin = Column(Boolean, default=False)
    
    # Hierarchical references
    law_source_id = Column(Integer, ForeignKey("law_sources.id"))
    branch_id = Column(Integer, ForeignKey("law_branches.id"))
    chapter_id = Column(Integer, ForeignKey("law_chapters.id"))
    article_id = Column(Integer, ForeignKey("law_articles.id"))
    case_id = Column(Integer, ForeignKey("legal_cases.id"))
    term_id = Column(Integer, ForeignKey("legal_terms.id"))
    
    created_at = Column(DateTime, server_default=func.now())
```

---

## 🧠 AI Processing Details

### Gemini AI Configuration

```python
Model: "gemini-2.5-flash"
Timeout: 60 seconds
API: Official Google Generative AI SDK
```

### Legal Indicators (Arabic)

The system identifies legally meaningful text using these indicators:
```python
legal_indicators = [
    'يجب',      # must
    'يلزم',     # obligated
    'يجوز',     # permitted
    'يعاقب',    # punished
    'يحكم',     # judged
    'يشترط',    # required
    'مادة',     # article
    'قانون',    # law
    'نظام',     # system
    'عقوبة',    # penalty
    'تعويض',    # compensation
    'حق',       # right
    'التزام',   # obligation
    'مسؤولية',  # responsibility
    'عقد',      # contract
    'اتفاق',    # agreement
    'محكمة'     # court
]
```

### Fallback Mechanism

If Gemini AI fails, the system uses punctuation-based splitting:
```python
# Arabic and English punctuation
sentences = re.split(r'[\.!?،؛]', text)
```

---

## 🔐 Authentication & Authorization

All endpoints require JWT authentication:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Authentication Flow:**
1. User sends request with JWT token
2. `get_current_user` dependency validates token
3. Returns `User` object if valid
4. Raises 401 Unauthorized if invalid

---

## ⚠️ Error Handling

### Error Response Format

```json
{
  "success": false,
  "message": "Human-readable error message",
  "data": null,
  "errors": [
    {
      "field": "document_id",
      "message": "Specific error details"
    }
  ]
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful processing |
| 400 | Bad Request | Document not found, no chunks |
| 401 | Unauthorized | Missing/invalid authentication |
| 500 | Internal Server Error | Database errors, AI failures |

### Error Scenarios

1. **Document Not Found**
   ```json
   {
     "success": false,
     "message": "Document with ID 123 not found",
     "errors": [{"field": "document_id", "message": "Document not found"}]
   }
   ```

2. **No Chunks Found**
   ```json
   {
     "success": false,
     "message": "No chunks found for document 123",
     "errors": [{"field": "document_id", "message": "No chunks found"}]
   }
   ```

3. **Processing Failed**
   ```json
   {
     "success": false,
     "message": "Processing failed: <error details>",
     "errors": [{"field": null, "message": "<error details>"}]
   }
   ```

---

## 📊 Performance Considerations

### Optimization Strategies

1. **Batch Processing**
   - Chunks saved in batches, not individually
   - Reduces database round trips

2. **Timeout Protection**
   - 60-second timeout for Gemini AI calls
   - Prevents hanging requests

3. **Lazy Initialization**
   - Gemini client initialized only when needed
   - Reduces startup time

4. **Fallback Mechanism**
   - If AI fails, uses simple splitting
   - Ensures processing completes

### Expected Performance

| Metric | Value |
|--------|-------|
| Average chunk processing | 2-5 seconds |
| Gemini AI timeout | 60 seconds max |
| Batch save time | < 1 second |
| Total for 10 chunks | 20-50 seconds |

---

## 🧪 Testing Examples

### Example 1: Process a Document

```bash
curl -X POST "http://localhost:8000/api/v1/chunks/documents/1/process" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json"
```

### Example 2: Check Processing Status

```bash
curl -X GET "http://localhost:8000/api/v1/chunks/documents/1/status" \
  -H "Authorization: Bearer your_token_here"
```

### Example 3: Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/chunks"
TOKEN = "your_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Process document
response = requests.post(
    f"{BASE_URL}/documents/1/process",
    headers=headers
)
result = response.json()
print(f"Processed: {result['data']['new_smart_chunks_count']} chunks")

# Check status
response = requests.get(
    f"{BASE_URL}/documents/1/status",
    headers=headers
)
status = response.json()
print(f"Progress: {status['data']['processing_progress']}")
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
DATABASE_URL=sqlite:///./app.db
JWT_SECRET=your_secret_key
```

### Getting Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env` file

---

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DATABASE_URL=sqlite:///./app.db
    volumes:
      - ./app.db:/app/app.db
```

---

## 📈 Future Enhancements

### Planned Features

1. **Vector Embeddings**
   - Generate embeddings using Gemini
   - Store in vector database (FAISS/Qdrant)
   - Enable semantic search

2. **Batch Processing**
   - Process multiple documents at once
   - Background job queue (Celery)
   - Progress tracking

3. **Chunk Verification**
   - Admin review interface
   - Manual chunk editing
   - Quality scoring

4. **Advanced Filtering**
   - Configurable legal indicators
   - Custom splitting rules
   - Language detection

5. **Analytics Dashboard**
   - Processing statistics
   - Quality metrics
   - Performance monitoring

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Gemini SDK Not Found

```bash
Error: ModuleNotFoundError: No module named 'google.genai'
```

**Solution:**
```bash
pip install google-generativeai
```

#### 2. API Key Invalid

```bash
Error: Gemini SDK not available: Invalid API key
```

**Solution:**
- Check `.env` file has `GEMINI_API_KEY`
- Verify key is valid at Google AI Studio
- Restart server after adding key

#### 3. Timeout Errors

```bash
Error: Gemini API timeout
```

**Solution:**
- Check internet connection
- Verify Gemini API is accessible
- System uses fallback automatically

#### 4. Database Constraint Errors

```bash
Error: CHECK constraint failed: status IN ('raw', 'processed', 'indexed')
```

**Solution:**
- Ensure status values match model constraints
- Check database schema matches model

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini AI Documentation](https://ai.google.dev/docs)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## 👥 Contributors

- AI-powered text processing
- Clean architecture implementation
- Comprehensive error handling
- Unified API responses

---

## 📝 License

This system is part of the Legatoo Legal Platform.

---

## 🎯 Summary

The Chunk Processing System provides:

✅ **AI-Powered Splitting** - Uses Gemini to create meaningful chunks  
✅ **Robust Error Handling** - Fallback mechanisms ensure reliability  
✅ **Clean Architecture** - Separation of concerns (Router → Service → Repository)  
✅ **Unified Responses** - Consistent API response structure  
✅ **Async Operations** - Non-blocking processing for better performance  
✅ **Authentication** - JWT-based security  
✅ **Logging** - Comprehensive logging for debugging  
✅ **Type Safety** - Full type hints and validation  

---

**Last Updated:** October 8, 2024  
**Version:** 1.0.0
