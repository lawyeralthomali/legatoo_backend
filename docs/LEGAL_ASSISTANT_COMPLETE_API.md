# Legal Assistant Complete API Documentation

## Overview

The Legal Assistant Complete API provides comprehensive functionality for managing legal documents, including upload, retrieval, search, update, and deletion operations. All endpoints follow the unified API response format and include proper authentication and validation.

## Base URL

All endpoints are prefixed with `/api/v1/legal-assistant`

## Authentication

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## API Response Format

All endpoints return responses in the unified format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  },
  "errors": []
}
```

Error responses:
```json
{
  "success": false,
  "message": "Error description",
  "data": null,
  "errors": [
    {
      "field": "field_name",
      "message": "Specific error message"
    }
  ]
}
```

## Endpoints

### 1. Upload Legal Document

**POST** `/api/v1/legal-assistant/documents/upload`

Upload a legal document for processing and indexing.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:**
  - `file` (required): Legal document file (PDF, DOCX, TXT)
  - `title` (required): Document title (1-255 characters)
  - `document_type` (optional): Type of legal document
  - `language` (optional): Document language (ar, en, fr)
  - `notes` (optional): Additional notes
  - `process_immediately` (optional): Process immediately (default: true)

**Supported File Types:**
- PDF (.pdf)
- Microsoft Word (.docx, .doc)
- Text files (.txt)

**File Size Limit:** 10MB

**Response:**
```json
{
  "success": true,
  "message": "Document uploaded successfully",
  "data": {
    "document": {
      "id": 1,
      "title": "Saudi Labor Law 2023",
      "file_path": "uploads/legal_documents/uuid.pdf",
      "document_type": "labor_law",
      "language": "ar",
      "processing_status": "pending",
      "is_processed": false,
      "notes": "Updated labor law regulations",
      "created_at": "2024-01-01T00:00:00Z",
      "uploaded_by_id": 1
    },
    "upload_info": {
      "filename": "labor_law.pdf",
      "file_size": 2048576,
      "file_type": ".pdf",
      "process_immediately": true,
      "uploaded_by": "user@example.com"
    }
  },
  "errors": []
}
```

### 2. Get Legal Documents

**GET** `/api/v1/legal-assistant/documents`

Retrieve legal documents with filtering and pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1, min: 1)
- `page_size` (optional): Items per page (default: 20, min: 1, max: 100)
- `document_type` (optional): Filter by document type
- `language` (optional): Filter by language
- `processing_status` (optional): Filter by processing status
- `search` (optional): Search in document titles
- `uploaded_by` (optional): Filter by uploader user ID

**Document Types:**
- `employment_contract`
- `partnership_contract`
- `service_contract`
- `lease_contract`
- `sales_contract`
- `labor_law`
- `commercial_law`
- `civil_law`
- `other`

**Languages:**
- `ar` (Arabic)
- `en` (English)
- `fr` (French)

**Processing Status:**
- `pending`
- `processing`
- `done`
- `error`

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 5 documents",
  "data": {
    "documents": [
      {
        "id": 1,
        "title": "Saudi Labor Law 2023",
        "file_path": "uploads/legal_documents/uuid.pdf",
        "document_type": "labor_law",
        "language": "ar",
        "processing_status": "done",
        "is_processed": true,
        "notes": "Updated labor law regulations",
        "created_at": "2024-01-01T00:00:00Z",
        "uploaded_by_id": 1
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 5,
      "total_pages": 1,
      "has_next": false,
      "has_previous": false
    },
    "filters": {
      "document_type": "labor_law",
      "language": "ar",
      "processing_status": null,
      "search": null,
      "uploaded_by": null
    }
  },
  "errors": []
}
```

### 3. Get Specific Document

**GET** `/api/v1/legal-assistant/documents/{document_id}`

Retrieve a specific legal document by ID.

**Path Parameters:**
- `document_id` (required): Document ID

**Query Parameters:**
- `include_chunks` (optional): Include document chunks (default: false)

**Response:**
```json
{
  "success": true,
  "message": "Document retrieved successfully",
  "data": {
    "document": {
      "id": 1,
      "title": "Saudi Labor Law 2023",
      "file_path": "uploads/legal_documents/uuid.pdf",
      "document_type": "labor_law",
      "language": "ar",
      "processing_status": "done",
      "is_processed": true,
      "notes": "Updated labor law regulations",
      "created_at": "2024-01-01T00:00:00Z",
      "uploaded_by_id": 1
    },
    "chunks": [
      {
        "id": 1,
        "chunk_index": 1,
        "content": "المادة الأولى: يهدف هذا النظام إلى...",
        "article_number": "المادة 1",
        "section_title": "الأهداف",
        "keywords": ["نظام العمل", "حقوق العامل"],
        "similarity_score": null,
        "is_rtl": true,
        "text_direction": "rtl",
        "formatted_content": "<div dir='rtl'>المادة الأولى: يهدف هذا النظام إلى...</div>",
        "normalized_content": "المادة الأولى: يهدف هذا النظام إلى..."
      }
    ],
    "chunks_count": 1
  },
  "errors": []
}
```

### 4. Update Document

**PUT** `/api/v1/legal-assistant/documents/{document_id}`

Update legal document metadata.

**Path Parameters:**
- `document_id` (required): Document ID

**Request Body:**
```json
{
  "title": "Updated Document Title",
  "document_type": "labor_law",
  "language": "ar",
  "notes": "Updated notes"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Document updated successfully",
  "data": {
    "document": {
      "id": 1,
      "title": "Updated Document Title",
      "file_path": "uploads/legal_documents/uuid.pdf",
      "document_type": "labor_law",
      "language": "ar",
      "processing_status": "done",
      "is_processed": true,
      "notes": "Updated notes",
      "created_at": "2024-01-01T00:00:00Z",
      "uploaded_by_id": 1
    }
  },
  "errors": []
}
```

### 5. Delete Document

**DELETE** `/api/v1/legal-assistant/documents/{document_id}`

Delete a legal document and all associated data.

**Path Parameters:**
- `document_id` (required): Document ID

**Query Parameters:**
- `delete_file` (optional): Delete file from filesystem (default: true)

**Response:**
```json
{
  "success": true,
  "message": "Document deleted successfully",
  "data": {
    "document_id": 1,
    "document_title": "Saudi Labor Law 2023",
    "chunks_deleted": 5,
    "file_deleted": true,
    "deleted_by": "user@example.com"
  },
  "errors": []
}
```

### 6. Search Documents

**POST** `/api/v1/legal-assistant/documents/search`

Search legal documents using semantic search.

**Request Body:**
```json
{
  "query": "ما هي حقوق العامل في الإجازات السنوية؟",
  "document_type": "labor_law",
  "language": "ar",
  "article_number": "المادة 50",
  "limit": 10,
  "similarity_threshold": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "message": "Found 3 results",
  "data": {
    "results": [
      {
        "chunk": {
          "id": 15,
          "chunk_index": 3,
          "content": "المادة الخمسون: للعامل الحق في إجازة سنوية مدفوعة الأجر...",
          "article_number": "المادة 50",
          "section_title": "الإجازات",
          "keywords": ["إجازة سنوية", "حقوق العامل"],
          "similarity_score": 0.95,
          "is_rtl": true,
          "text_direction": "rtl",
          "formatted_content": "<div dir='rtl'>المادة الخمسون: للعامل الحق في إجازة سنوية مدفوعة الأجر...</div>",
          "normalized_content": "المادة الخمسون: للعامل الحق في إجازة سنوية مدفوعة الأجر..."
        },
        "document": {
          "id": 1,
          "title": "Saudi Labor Law 2023",
          "file_path": "uploads/legal_documents/uuid.pdf",
          "document_type": "labor_law",
          "language": "ar",
          "processing_status": "done",
          "is_processed": true,
          "notes": "Updated labor law regulations",
          "created_at": "2024-01-01T00:00:00Z",
          "uploaded_by_id": 1
        },
        "similarity_score": 0.95,
        "highlights": ["حقوق العامل", "إجازة سنوية"]
      }
    ],
    "total_found": 3,
    "query": "ما هي حقوق العامل في الإجازات السنوية؟",
    "filters": {
      "document_type": "labor_law",
      "language": "ar",
      "article_number": "المادة 50",
      "similarity_threshold": 0.7
    }
  },
  "errors": []
}
```

### 7. Get Document Statistics

**GET** `/api/v1/legal-assistant/documents/statistics`

Get comprehensive statistics about legal documents.

**Response:**
```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "total_documents": 25,
    "total_chunks": 150,
    "documents_by_type": {
      "labor_law": 10,
      "commercial_law": 8,
      "civil_law": 5,
      "other": 2
    },
    "documents_by_language": {
      "ar": 20,
      "en": 5
    },
    "processing_pending": 2,
    "processing_done": 22,
    "processing_error": 1,
    "processing_in_progress": 0
  },
  "errors": []
}
```

### 8. Get Processing Status

**GET** `/api/v1/legal-assistant/documents/{document_id}/processing-status`

Get the processing status of a legal document.

**Path Parameters:**
- `document_id` (required): Document ID

**Response:**
```json
{
  "success": true,
  "message": "Processing status retrieved successfully",
  "data": {
    "document_id": 1,
    "document_title": "Saudi Labor Law 2023",
    "processing_status": "done",
    "is_processed": true,
    "progress": {
      "status": "done",
      "progress_percentage": 100.0,
      "chunks_processed": 15,
      "total_chunks": 15,
      "message": "Processing completed successfully",
      "error": null
    }
  },
  "errors": []
}
```

### 9. Reprocess Document

**POST** `/api/v1/legal-assistant/documents/{document_id}/reprocess`

Trigger reprocessing of a legal document.

**Path Parameters:**
- `document_id` (required): Document ID

**Query Parameters:**
- `force_reprocess` (optional): Force reprocessing even if already processed (default: false)

**Response:**
```json
{
  "success": true,
  "message": "Document reprocessing started successfully",
  "data": {
    "document_id": 1,
    "status": "processing_started",
    "document_title": "Saudi Labor Law 2023",
    "force_reprocess": false
  },
  "errors": []
}
```

### 10. Download Document

**GET** `/api/v1/legal-assistant/documents/{document_id}/download`

Download the original legal document file.

**Path Parameters:**
- `document_id` (required): Document ID

**Response:**
- **Content-Type:** Based on file type (application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, etc.)
- **Content-Disposition:** attachment; filename="document_name.ext"
- **Body:** Binary file content

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "success": false,
  "message": "Invalid input data",
  "data": null,
  "errors": [
    {
      "field": "title",
      "message": "Title is required"
    }
  ]
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "message": "Authentication required",
  "data": null,
  "errors": [
    {
      "field": null,
      "message": "Invalid or missing authentication token"
    }
  ]
}
```

**404 Not Found:**
```json
{
  "success": false,
  "message": "Document not found",
  "data": null,
  "errors": [
    {
      "field": "document_id",
      "message": "Document not found"
    }
  ]
}
```

**413 Payload Too Large:**
```json
{
  "success": false,
  "message": "File size exceeds limit",
  "data": null,
  "errors": [
    {
      "field": "file",
      "message": "File size must be less than 10MB"
    }
  ]
}
```

**415 Unsupported Media Type:**
```json
{
  "success": false,
  "message": "Unsupported file format: .txt",
  "data": null,
  "errors": [
    {
      "field": "file",
      "message": "Supported formats: .pdf, .docx, .doc, .txt"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "message": "Internal server error",
  "data": null,
  "errors": [
    {
      "field": null,
      "message": "An unexpected error occurred"
    }
  ]
}
```

## Features

### Document Processing
- **Multi-format Support:** PDF, DOCX, DOC, TXT
- **OCR Support:** Image files (JPG, JPEG, PNG) with OCR processing
- **Intelligent Chunking:** Automatic text segmentation (300-500 words)
- **Embedding Generation:** Vector embeddings for semantic search
- **FAISS Indexing:** Fast vector search capabilities

### Search Capabilities
- **Semantic Search:** AI-powered semantic search using embeddings
- **Multi-language Support:** Arabic, English, French
- **Filtering:** By document type, language, article number
- **Similarity Scoring:** Configurable similarity thresholds
- **Highlighting:** Search term highlighting in results

### Arabic Text Processing
- **RTL Support:** Right-to-left text direction handling
- **Text Normalization:** Arabic text normalization and cleaning
- **Keyword Extraction:** Automatic Arabic keyword extraction
- **Formatted Output:** HTML-formatted content with proper direction

### Security & Validation
- **Authentication:** JWT-based authentication
- **File Validation:** Type and size validation
- **Input Validation:** Comprehensive request validation
- **Error Handling:** Detailed error messages with field-specific errors

## Usage Examples

### Upload a Document
```bash
curl -X POST "http://localhost:8000/api/v1/legal-assistant/documents/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@labor_law.pdf" \
  -F "title=Saudi Labor Law 2023" \
  -F "document_type=labor_law" \
  -F "language=ar" \
  -F "notes=Updated labor law regulations"
```

### Search Documents
```bash
curl -X POST "http://localhost:8000/api/v1/legal-assistant/documents/search" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ما هي حقوق العامل في الإجازات السنوية؟",
    "document_type": "labor_law",
    "language": "ar",
    "limit": 5,
    "similarity_threshold": 0.7
  }'
```

### Get Documents with Filtering
```bash
curl -X GET "http://localhost:8000/api/v1/legal-assistant/documents?page=1&page_size=10&document_type=labor_law&language=ar" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Integration Notes

- All endpoints follow the unified API response format
- Authentication is required for all operations
- File uploads support multipart/form-data
- Search results include similarity scores and highlighting
- Arabic text is properly handled with RTL support
- Processing is asynchronous with status tracking
- Comprehensive error handling with field-specific errors
