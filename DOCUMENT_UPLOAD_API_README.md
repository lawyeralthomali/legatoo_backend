# Legal Document Upload API

A comprehensive FastAPI endpoint for uploading and processing legal documents with hierarchical parsing, metadata extraction, and knowledge chunking.

## 🚀 Features

- **Multi-format Support**: JSON (fully implemented), PDF/DOCX/TXT (planned)
- **Hierarchical Processing**: Law Sources → Articles → Knowledge Chunks
- **Duplicate Detection**: SHA-256 hash-based duplicate prevention
- **Bulk Operations**: Optimized database operations with transaction safety
- **Comprehensive Validation**: File type, size, structure, and content validation
- **Real-time Statistics**: Processing time, chunk counts, and performance metrics
- **Error Handling**: Detailed error messages with field-specific validation
- **Modular Design**: Extensible architecture for future file type support

## 📁 Project Structure

```
app/
├── schemas/
│   └── document_upload.py          # Pydantic schemas for request/response
├── services/
│   └── document_parser_service.py  # Core parsing and upload logic
├── routes/
│   └── document_upload_router.py   # FastAPI endpoint definitions
├── docs/
│   └── document_upload_examples.py # Documentation and examples
└── main.py                        # Router registration
```

## 🔧 Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic python-multipart
   ```

2. **Register Router** (already done in `main.py`):
   ```python
   from .routes.document_upload_router import router as document_upload_router
   app.include_router(document_upload_router)
   ```

3. **Start Server**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📚 API Endpoints

### 1. Upload Document
**POST** `/api/v1/documents/upload`

Upload and process a legal document.

**Parameters:**
- `file`: Document file (multipart/form-data, required)
- `title`: Document title (string, required)
- `category`: Document category (string, required)
- `uploaded_by`: User ID (integer, optional)

**Categories:** `law`, `article`, `manual`, `policy`, `contract`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@labor_law.json" \
  -F "title=نظام العمل السعودي 2023" \
  -F "category=law" \
  -F "uploaded_by=1"
```

### 2. Get Upload Status
**GET** `/api/v1/documents/upload/status/{document_id}`

Get processing status and statistics for a document.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents/upload/status/123"
```

### 3. Get Supported Formats
**GET** `/api/v1/documents/supported-formats`

Get information about supported file formats and capabilities.

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/documents/supported-formats"
```

## 📄 JSON Document Structure

Your JSON file must follow this structure:

```json
{
    "law_sources": [
        {
            "name": "Law Name",
            "type": "law|regulation|code|directive|decree",
            "jurisdiction": "Jurisdiction",
            "issuing_authority": "Authority",
            "issue_date": "YYYY-MM-DD",
            "last_update": "YYYY-MM-DD",
            "description": "Description",
            "source_url": "URL",
            "articles": [
                {
                    "article": "Article Number",
                    "title": "Article Title",
                    "text": "Article Content",
                    "keywords": ["keyword1", "keyword2"],
                    "order_index": 1
                }
            ]
        }
    ]
}
```

## 🔄 Processing Flow

1. **File Validation**: Check file type, size, and format
2. **Duplicate Detection**: Calculate SHA-256 hash and check for duplicates
3. **Document Creation**: Create `KnowledgeDocument` record
4. **Content Parsing**: Parse JSON structure and extract legal entities
5. **Database Operations**: 
   - Create/update `LawSource` records
   - Create/update `LawArticle` records
   - Create `KnowledgeChunk` records with hierarchical references
6. **Status Update**: Mark document as processed
7. **Response Generation**: Return comprehensive processing results

## 📊 Response Format

All responses follow the unified API response format:

```json
{
    "success": true|false,
    "message": "Human-readable message",
    "data": {
        "document_id": 123,
        "title": "Document Title",
        "category": "law",
        "file_path": "uploads/file.json",
        "file_hash": "sha256_hash",
        "status": "processed",
        "uploaded_at": "2024-12-01T14:30:22Z",
        "chunks_created": 15,
        "law_sources_processed": 2,
        "articles_processed": 4,
        "law_sources": [...],
        "articles": [...],
        "chunks": [...],
        "processing_time_seconds": 2.34,
        "file_size_bytes": 15420,
        "duplicate_detected": false
    },
    "errors": []
}
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python test_document_upload_api.py
```

The test script includes:
- Document upload testing
- Status checking
- Error case validation
- Supported formats verification

## 🏗️ Architecture

### Modular Design

The implementation follows a modular architecture:

1. **Schemas** (`document_upload.py`): Pydantic models for validation
2. **Services** (`document_parser_service.py`): Core business logic
3. **Routes** (`document_upload_router.py`): API endpoint definitions
4. **Models** (`legal_knowledge.py`): Database models (existing)

### Extensibility

The parser service is designed for easy extension:

```python
class LegalDocumentParser:
    async def parse_document(self, file_path, document, metadata):
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.json':
            return await self._parse_json_document(file_path, document, metadata)
        elif file_extension == '.pdf':
            return await self._parse_pdf_document(file_path, document, metadata)
        # ... other formats
```

### Database Operations

- **Bulk Operations**: Efficient batch processing
- **Transaction Safety**: Rollback on errors
- **Relationship Integrity**: Proper foreign key handling
- **Duplicate Prevention**: Hash-based duplicate detection

## 🔒 Security & Validation

- **File Type Validation**: Only allowed extensions accepted
- **File Size Limits**: 50MB maximum file size
- **Content Validation**: JSON structure validation
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **Input Sanitization**: Pydantic model validation

## 📈 Performance

- **Memory Efficient**: Streaming file processing
- **Bulk Database Operations**: Reduced database round trips
- **Optimized Chunking**: Efficient text segmentation
- **Background Processing**: Non-blocking operations (planned)

## 🚧 Future Enhancements

### Planned Features

1. **PDF Support** (Q2 2024):
   - Text extraction using PyPDF2/pdfplumber
   - Layout analysis for structured content
   - OCR support for scanned documents

2. **DOCX Support** (Q2 2024):
   - Document structure parsing
   - Table and list processing
   - Formatting preservation

3. **TXT Support** (Q1 2024):
   - Text structure detection
   - Article/section identification
   - Basic legal document formatting

4. **Advanced Features**:
   - NLP-based chunking strategies
   - Multi-language support
   - Document versioning
   - Batch upload processing
   - Real-time progress tracking

## 🐛 Error Handling

The API provides comprehensive error handling:

- **Validation Errors**: Field-specific error messages
- **File Errors**: Type, size, and format validation
- **Processing Errors**: Detailed error reporting
- **Database Errors**: Transaction rollback and error logging

## 📝 Logging

Comprehensive logging throughout the process:

- **Upload Events**: File validation and storage
- **Processing Events**: Parsing and database operations
- **Error Events**: Detailed error logging
- **Performance Events**: Timing and statistics

## 🤝 Contributing

To extend the API:

1. **Add New File Type**: Implement parser method in `LegalDocumentParser`
2. **Add Validation**: Extend Pydantic schemas
3. **Add Endpoints**: Create new routes in the router
4. **Add Tests**: Update test suite

## 📄 License

This implementation follows the project's existing license and coding standards.

---

**Note**: This API is designed to integrate seamlessly with the existing legal knowledge management system and follows all established patterns and conventions.
