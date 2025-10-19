# Legal AI Assistant - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `python-docx` - For DOCX file processing
- `numpy` - For vector operations
- `openai` - For OpenAI embeddings (optional)

### Step 2: Configure Environment

Create or update your `.env` file:

```bash
# Required for best results (Optional but recommended)
OPENAI_API_KEY=your-openai-api-key-here

# Optional configurations
EMBEDDING_MODEL=text-embedding-3-large
UPLOAD_DIR=uploads/legal_documents
MAX_UPLOAD_SIZE=52428800
```

**Without OpenAI API:**
The system will use local fallback embeddings (lower quality but functional).

### Step 3: Run Database Migration

```bash
alembic upgrade head
```

This creates the required tables:
- `legal_documents` - Document metadata
- `legal_document_chunks` - Document chunks with embeddings

### Step 4: Start the Server

```bash
uvicorn app.main:app --reload
```

Server will start on: `http://localhost:8000`

### Step 5: Test the API

#### Option A: Interactive Docs (Recommended)

1. Open: `http://localhost:8000/docs`
2. Click "Authorize" and enter your JWT token
3. Try the endpoints under "Legal Assistant"

#### Option B: Command Line

**Upload a document:**
```bash
curl -X POST "http://localhost:8000/api/v1/legal-assistant/documents/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@path/to/document.pdf" \
  -F "title=My Legal Document" \
  -F "document_type=labor_law" \
  -F "language=ar" \
  -F "process_immediately=true"
```

**Search documents:**
```bash
curl -X POST "http://localhost:8000/api/v1/legal-assistant/documents/search" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "حقوق العامل في الإجازات السنوية",
    "document_type": "labor_law",
    "language": "ar",
    "limit": 5,
    "similarity_threshold": 0.7
  }'
```

**Get statistics:**
```bash
curl -X GET "http://localhost:8000/api/v1/legal-assistant/statistics" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📋 Available Endpoints

All endpoints are under `/api/v1/legal-assistant`:

### Document Management
- `POST /documents/upload` - Upload new document
- `GET /documents` - List all documents (with filters)
- `GET /documents/{id}` - Get document details
- `PUT /documents/{id}` - Update document
- `DELETE /documents/{id}` - Delete document

### Search
- `POST /documents/search` - Semantic search

### Chunks
- `GET /documents/{id}/chunks` - Get document chunks
- `GET /chunks/{id}` - Get chunk details

### Monitoring
- `GET /documents/{id}/progress` - Processing progress
- `GET /statistics` - System statistics
- `POST /documents/{id}/reprocess` - Reprocess document

## 🎯 Common Use Cases

### Use Case 1: Upload and Process Legal Document

```python
import httpx
import asyncio

async def upload_document():
    async with httpx.AsyncClient() as client:
        # Upload
        with open("saudi_labor_law.pdf", "rb") as f:
            response = await client.post(
                "http://localhost:8000/api/v1/legal-assistant/documents/upload",
                headers={"Authorization": "Bearer YOUR_TOKEN"},
                files={"file": f},
                data={
                    "title": "Saudi Labor Law 2023",
                    "document_type": "labor_law",
                    "language": "ar",
                    "process_immediately": True
                }
            )
        
        doc = response.json()["data"]
        print(f"Uploaded: {doc['id']}")
        
        # Check progress
        await asyncio.sleep(5)
        progress_response = await client.get(
            f"http://localhost:8000/api/v1/legal-assistant/documents/{doc['id']}/progress",
            headers={"Authorization": "Bearer YOUR_TOKEN"}
        )
        
        progress = progress_response.json()["data"]
        print(f"Progress: {progress['progress_percentage']}%")

asyncio.run(upload_document())
```

### Use Case 2: Search for Legal Information

```python
async def search_legal_info():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/legal-assistant/documents/search",
            headers={"Authorization": "Bearer YOUR_TOKEN"},
            json={
                "query": "ما هي حقوق العامل في الإجازات السنوية؟",
                "document_type": "labor_law",
                "language": "ar",
                "limit": 5,
                "similarity_threshold": 0.7
            }
        )
        
        results = response.json()["data"]
        print(f"Found {results['total_found']} results in {results['query_time_ms']}ms")
        
        for result in results['results']:
            print(f"\nArticle {result['chunk']['article_number']}")
            print(f"Score: {result['similarity_score']:.2f}")
            print(f"Text: {result['chunk']['content'][:200]}...")

asyncio.run(search_legal_info())
```

### Use Case 3: Get System Statistics

```python
async def get_stats():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/legal-assistant/statistics",
            headers={"Authorization": "Bearer YOUR_TOKEN"}
        )
        
        stats = response.json()["data"]
        print(f"Total Documents: {stats['total_documents']}")
        print(f"Total Chunks: {stats['total_chunks']}")
        print(f"Processing Done: {stats['processing_done']}")
        print(f"\nDocuments by Type:")
        for doc_type, count in stats['documents_by_type'].items():
            print(f"  {doc_type}: {count}")

asyncio.run(get_stats())
```

## ⚡ Performance Tips

1. **Enable OpenAI API** for best search quality
2. **Batch uploads** for multiple documents
3. **Use filters** to narrow search space
4. **Adjust similarity threshold** based on needs (0.5-0.9)
5. **Monitor progress** for long documents

## 🔍 Testing Checklist

- [ ] Server starts without errors
- [ ] Can access `/docs` endpoint
- [ ] Authentication works
- [ ] Can upload PDF document
- [ ] Document processing completes
- [ ] Can search and get results
- [ ] Can view document chunks
- [ ] Statistics endpoint works

## 🐛 Troubleshooting

### Issue: "No module named 'docx'"
```bash
pip install python-docx
```

### Issue: "OPENAI_API_KEY not found"
- Add to `.env` file OR
- System will use fallback embeddings (lower quality)

### Issue: "File upload fails"
- Check file size (max 50MB)
- Verify file format (.pdf, .docx, .doc, .txt)
- Ensure upload directory exists

### Issue: "Search returns no results"
- Wait for processing to complete (check `/progress`)
- Lower similarity_threshold (try 0.5)
- Check if language matches

## 📚 Next Steps

1. ✅ Read full documentation: `docs/LEGAL_ASSISTANT_README.md`
2. ✅ Review implementation: `docs/LEGAL_ASSISTANT_IMPLEMENTATION_SUMMARY.md`
3. ✅ Explore API in `/docs` interface
4. ✅ Upload your first legal document
5. ✅ Try semantic search

## 🎉 You're Ready!

The Legal AI Assistant is now fully functional and ready to:
- Process legal documents in Arabic and English
- Provide fast semantic search
- Extract legal entities and metadata
- Handle thousands of documents efficiently

**Happy searching! 🚀**

