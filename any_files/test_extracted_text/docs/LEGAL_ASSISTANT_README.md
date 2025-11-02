# Legal AI Assistant - Documentation

## Overview

The Legal AI Assistant is a high-performance document processing and semantic search system designed for Arabic and English legal documents. It provides intelligent chunking, multilingual embeddings, and fast semantic search capabilities.

## Features

### 🚀 Core Capabilities

1. **Document Upload & Processing**
   - Support for PDF, DOC, DOCX, and TXT files
   - Asynchronous processing for large documents
   - Intelligent text extraction preserving legal context
   - Automatic language detection (Arabic, English, French)

2. **Intelligent Chunking**
   - Context-aware splitting (200-500 words per chunk)
   - Preserves sentence and paragraph boundaries
   - Maintains legal structure (articles, sections, clauses)
   - Configurable chunk size and overlap

3. **Legal Entity Extraction**
   - Automatic detection of article numbers
   - Section and chapter identification
   - Keyword extraction for both Arabic and English
   - Metadata tagging for efficient filtering

4. **Multilingual Embeddings**
   - OpenAI text-embedding-3-large support
   - High-quality semantic representations
   - Arabic and English language support
   - Fallback to local embeddings

5. **Hybrid Search**
   - Vector similarity search (semantic)
   - Keyword-based filtering
   - Metadata filtering (type, language, articles)
   - Configurable similarity thresholds

6. **Performance Optimizations**
   - Async/await throughout the stack
   - Batch embedding generation
   - Efficient database queries
   - Millisecond-level search latency

## Architecture

### Layer Structure

```
┌─────────────────────────────────────┐
│       API Layer (Routes)            │
│   - legal_assistant_router.py       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Service Layer (Business Logic)  │
│   - LegalAssistantService           │
│   - DocumentProcessingService       │
│   - EmbeddingService                │
│   - SemanticSearchService           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Repository Layer (Data Access)   │
│   - LegalDocumentRepository         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Database Layer (Models)        │
│   - LegalDocument                   │
│   - LegalDocumentChunk              │
└─────────────────────────────────────┘
```

### SOLID Principles Applied

1. **Single Responsibility**: Each service has one clear purpose
2. **Open/Closed**: Extensible through interfaces
3. **Liskov Substitution**: Repository pattern allows easy testing
4. **Interface Segregation**: Focused interfaces for each concern
5. **Dependency Inversion**: Services depend on abstractions

## API Endpoints

### 1. Upload Document

```http
POST /api/v1/legal-assistant/documents/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

Parameters:
- file: UploadFile (PDF, DOC, DOCX, TXT)
- title: string (required)
- document_type: string (default: "other")
- language: string (default: "ar")
- notes: string (optional)
- process_immediately: boolean (default: true)

Response:
{
  "success": true,
  "message": "Document uploaded successfully",
  "data": {
    "id": 1,
    "title": "Saudi Labor Law 2023",
    "file_path": "uploads/legal_documents/uuid.pdf",
    "document_type": "labor_law",
    "language": "ar",
    "processing_status": "processing",
    "created_at": "2025-10-01T12:00:00Z"
  },
  "errors": []
}
```

### 2. Semantic Search

```http
POST /api/v1/legal-assistant/documents/search
Content-Type: application/json
Authorization: Bearer {token}

Body:
{
  "query": "ما هي حقوق العامل في الإجازات السنوية؟",
  "document_type": "labor_law",
  "language": "ar",
  "limit": 10,
  "similarity_threshold": 0.7
}

Response:
{
  "success": true,
  "message": "Found 5 relevant results",
  "data": {
    "results": [
      {
        "chunk": {
          "id": 123,
          "content": "المادة 109: يستحق العامل...",
          "article_number": "109",
          "keywords": ["إجازة", "سنوية", "عامل"]
        },
        "document": {
          "id": 1,
          "title": "Saudi Labor Law 2023",
          "document_type": "labor_law"
        },
        "similarity_score": 0.89,
        "highlights": ["يستحق العامل إجازة سنوية"]
      }
    ],
    "total_found": 5,
    "query_time_ms": 45.3,
    "query": "ما هي حقوق العامل في الإجازات السنوية؟"
  },
  "errors": []
}
```

### 3. Get Documents

```http
GET /api/v1/legal-assistant/documents?page=1&page_size=20&document_type=labor_law
Authorization: Bearer {token}

Response:
{
  "success": true,
  "message": "Retrieved 20 documents",
  "data": {
    "documents": [...],
    "total": 150,
    "page": 1,
    "page_size": 20
  },
  "errors": []
}
```

### 4. Get Document Details

```http
GET /api/v1/legal-assistant/documents/{document_id}
Authorization: Bearer {token}
```

### 5. Update Document

```http
PUT /api/v1/legal-assistant/documents/{document_id}
Content-Type: application/json
Authorization: Bearer {token}

Body:
{
  "title": "Updated Title",
  "document_type": "commercial_law",
  "notes": "Updated notes"
}
```

### 6. Delete Document

```http
DELETE /api/v1/legal-assistant/documents/{document_id}
Authorization: Bearer {token}
```

### 7. Get Document Chunks

```http
GET /api/v1/legal-assistant/documents/{document_id}/chunks?page=1&page_size=50
Authorization: Bearer {token}
```

### 8. Get Chunk Details

```http
GET /api/v1/legal-assistant/chunks/{chunk_id}
Authorization: Bearer {token}
```

### 9. Get Processing Progress

```http
GET /api/v1/legal-assistant/documents/{document_id}/progress
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": {
    "document_id": 1,
    "status": "processing",
    "progress_percentage": 65.5,
    "chunks_processed": 45,
    "total_chunks": 68,
    "message": "Processing chunks: 45/68"
  }
}
```

### 10. Get Statistics

```http
GET /api/v1/legal-assistant/statistics
Authorization: Bearer {token}

Response:
{
  "success": true,
  "data": {
    "total_documents": 150,
    "total_chunks": 12500,
    "documents_by_type": {
      "labor_law": 50,
      "commercial_law": 30,
      "civil_law": 70
    },
    "documents_by_language": {
      "ar": 120,
      "en": 30
    },
    "processing_pending": 5,
    "processing_done": 140,
    "processing_error": 5
  }
}
```

### 11. Reprocess Document

```http
POST /api/v1/legal-assistant/documents/{document_id}/reprocess
Authorization: Bearer {token}
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# OpenAI Configuration (Required for embeddings)
OPENAI_API_KEY=your-openai-api-key-here
EMBEDDING_MODEL=text-embedding-3-large

# File Upload Configuration
UPLOAD_DIR=uploads/legal_documents
MAX_UPLOAD_SIZE=52428800  # 50MB

# Database
DATABASE_URL=sqlite+aiosqlite:///./app.db
```

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- `python-docx`: DOCX file processing
- `PyPDF2`: PDF text extraction
- `httpx`: Async HTTP client for OpenAI
- `numpy`: Numerical operations
- `openai`: OpenAI API client (optional)

2. Create upload directory:
```bash
mkdir -p uploads/legal_documents
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the server:
```bash
uvicorn app.main:app --reload
```

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def upload_and_search():
    base_url = "http://localhost:8000/api/v1/legal-assistant"
    token = "your-jwt-token"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload document
    async with httpx.AsyncClient() as client:
        with open("saudi_labor_law.pdf", "rb") as f:
            files = {"file": f}
            data = {
                "title": "Saudi Labor Law 2023",
                "document_type": "labor_law",
                "language": "ar",
                "process_immediately": True
            }
            
            response = await client.post(
                f"{base_url}/documents/upload",
                files=files,
                data=data,
                headers=headers
            )
            
            doc = response.json()["data"]
            print(f"Uploaded document ID: {doc['id']}")
        
        # Wait for processing
        await asyncio.sleep(10)
        
        # Search
        search_payload = {
            "query": "حقوق العامل في الإجازات",
            "document_type": "labor_law",
            "language": "ar",
            "limit": 5,
            "similarity_threshold": 0.7
        }
        
        response = await client.post(
            f"{base_url}/documents/search",
            json=search_payload,
            headers=headers
        )
        
        results = response.json()["data"]
        print(f"Found {results['total_found']} results in {results['query_time_ms']}ms")
        
        for result in results['results']:
            print(f"\nArticle {result['chunk']['article_number']}")
            print(f"Score: {result['similarity_score']}")
            print(f"Content: {result['chunk']['content'][:200]}...")

asyncio.run(upload_and_search())
```

### JavaScript/TypeScript Example

```typescript
const baseUrl = 'http://localhost:8000/api/v1/legal-assistant';
const token = 'your-jwt-token';

// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'Saudi Labor Law 2023');
formData.append('document_type', 'labor_law');
formData.append('language', 'ar');

const uploadResponse = await fetch(`${baseUrl}/documents/upload`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const uploadData = await uploadResponse.json();
console.log('Document uploaded:', uploadData.data);

// Search
const searchResponse = await fetch(`${baseUrl}/documents/search`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'حقوق العامل في الإجازات',
    document_type: 'labor_law',
    language: 'ar',
    limit: 5,
    similarity_threshold: 0.7
  })
});

const searchData = await searchResponse.json();
console.log(`Found ${searchData.data.total_found} results`);
searchData.data.results.forEach(result => {
  console.log(`Article ${result.chunk.article_number}: ${result.similarity_score}`);
});
```

## Performance Optimization

### Current Performance

- **Upload**: < 1 second for files up to 10MB
- **Text Extraction**: ~2-5 seconds for 100-page PDF
- **Chunking**: ~1 second for 10,000 words
- **Embedding Generation**: ~1-2 seconds per chunk (OpenAI API)
- **Search**: < 100ms for queries against 10,000 chunks

### Optimization Tips

1. **Batch Processing**: Process multiple chunks in parallel
2. **Caching**: Cache frequently searched queries
3. **Vector Database**: Consider using dedicated vector DB (Pinecone, Weaviate) for large-scale deployments
4. **CDN**: Store files on CDN for faster access
5. **Background Jobs**: Use Celery or similar for async processing

## Future Enhancements

1. **Vector Database Integration**: Pinecone, Weaviate, or Qdrant for better scalability
2. **Advanced NLP**: Legal entity recognition, relationship extraction
3. **Summarization**: Auto-generate document summaries
4. **Document Comparison**: Compare two legal documents
5. **Citation Detection**: Find and link legal citations
6. **Multi-document Q&A**: Answer questions across multiple documents
7. **Export Features**: Export search results to PDF/Word
8. **Analytics Dashboard**: Usage statistics and insights

## Troubleshooting

### Common Issues

1. **"No OpenAI API key found"**
   - Add `OPENAI_API_KEY` to `.env` file
   - System falls back to local embeddings (lower quality)

2. **"File format not supported"**
   - Ensure file has `.pdf`, `.docx`, `.doc`, or `.txt` extension
   - Check file is not corrupted

3. **"Processing stuck at 0%"**
   - Check logs for errors
   - Verify file is readable
   - Ensure sufficient disk space

4. **"Search returns no results"**
   - Lower `similarity_threshold`
   - Check if documents are processed (`processing_status` = "done")
   - Verify language matches

## License

This project follows the main application license.

## Support

For issues or questions, please contact the development team or create an issue in the repository.

