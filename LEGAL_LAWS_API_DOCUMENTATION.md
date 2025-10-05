# Legal Laws Management API Documentation

## Overview
Complete RESTful API for managing legal laws with automatic PDF parsing, hierarchical structure extraction (Branches → Chapters → Articles), AI-powered analysis, and knowledge chunk creation.

**Base URL:** `/api/v1/laws`

**Authentication:** JWT Bearer Token required for all endpoints

---

## 📋 Table of Contents
1. [Upload and Parse Law](#1-upload-and-parse-law)
2. [List Laws](#2-list-laws)
3. [Get Law Tree](#3-get-law-tree)
4. [Get Law Metadata](#4-get-law-metadata)
5. [Update Law](#5-update-law)
6. [Delete Law](#6-delete-law)
7. [Reparse Law](#7-reparse-law)
8. [Analyze Law with AI](#8-analyze-law-with-ai)
9. [Get Law Statistics](#9-get-law-statistics)

---

## 1. Upload and Parse Law

### `POST /laws/upload`

Upload a PDF and automatically extract hierarchical structure.

#### **Workflow:**
1. Upload PDF file
2. Calculate SHA-256 hash (prevents duplicates)
3. Create `KnowledgeDocument` with file hash
4. Create `LawSource` linked to document
5. Parse PDF → Extract Branches → Chapters → Articles
6. Create `KnowledgeChunk` for each article
7. Update status to `'processed'`
8. Return full hierarchical tree

#### **Request:**
```http
POST /api/v1/laws/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

Form Data:
  law_name: "قانون العمل السعودي"
  law_type: "law"
  jurisdiction: "المملكة العربية السعودية"
  issuing_authority: "وزارة العمل"
  issue_date: "2005-04-23"
  last_update: "2023-02-14"
  description: "نظام العمل السعودي المعدل"
  source_url: "https://..."
  pdf_file: [Binary PDF file]
```

#### **Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `law_name` | string | ✅ Yes | Name of the law |
| `law_type` | enum | ✅ Yes | One of: `law`, `regulation`, `code`, `directive`, `decree` |
| `jurisdiction` | string | ❌ No | Jurisdiction (e.g., "Saudi Arabia") |
| `issuing_authority` | string | ❌ No | Authority that issued the law |
| `issue_date` | string | ❌ No | Issue date (YYYY-MM-DD format) |
| `last_update` | string | ❌ No | Last update date (YYYY-MM-DD) |
| `description` | string | ❌ No | Law description |
| `source_url` | string | ❌ No | Source URL |
| `pdf_file` | file | ✅ Yes | PDF or DOCX file to upload |

#### **Success Response (201):**
```json
{
  "success": true,
  "message": "Law uploaded and parsed successfully. Created 6 branches, 145 articles.",
  "data": {
    "law_source": {
      "id": 1,
      "name": "قانون العمل السعودي",
      "type": "law",
      "jurisdiction": "المملكة العربية السعودية",
      "issuing_authority": "وزارة العمل",
      "issue_date": "2005-04-23",
      "last_update": "2023-02-14",
      "description": "نظام العمل السعودي المعدل",
      "source_url": "https://...",
      "status": "processed",
      "branches": [
        {
          "id": 1,
          "branch_number": "5",
          "branch_name": "علاقات العمل",
          "description": null,
          "order_index": 0,
          "chapters": [
            {
              "id": 1,
              "chapter_number": "3",
              "chapter_name": "انتهاء عقد العمل",
              "description": null,
              "order_index": 0,
              "articles": [
                {
                  "id": 1,
                  "article_number": "75",
                  "title": "حالات إنهاء العقد",
                  "content": "يجوز لأي من طرفي عقد العمل إنهاؤه في الحالات التالية...",
                  "keywords": ["إنهاء", "عقد", "عمل"],
                  "order_index": 0,
                  "ai_processed_at": null,
                  "created_at": "2025-10-05T12:00:00Z"
                }
              ],
              "articles_count": 25
            }
          ],
          "chapters_count": 5
        }
      ],
      "branches_count": 6,
      "created_at": "2025-10-05T12:00:00Z",
      "updated_at": null
    }
  },
  "errors": []
}
```

#### **Error Responses:**

**Duplicate File (409):**
```json
{
  "success": false,
  "message": "Duplicate file detected. Document already exists: قانون العمل",
  "data": null,
  "errors": [
    {
      "field": "file_hash",
      "message": "File already uploaded as document ID 5"
    }
  ]
}
```

**Invalid File Type (400):**
```json
{
  "success": false,
  "message": "Invalid file type. Only PDF and DOCX files are supported",
  "data": null,
  "errors": []
}
```

**Invalid Law Type (400):**
```json
{
  "success": false,
  "message": "Invalid law_type. Must be one of: law, regulation, code, directive, decree",
  "data": null,
  "errors": []
}
```

**Parsing Failed (500):**
```json
{
  "success": false,
  "message": "Failed to parse PDF: No text could be extracted",
  "data": null,
  "errors": []
}
```

---

## 2. List Laws

### `GET /laws/`

List all laws with filtering and pagination.

#### **Request:**
```http
GET /api/v1/laws/?page=1&page_size=20&name=عمل&law_type=law&status=processed
Authorization: Bearer {token}
```

#### **Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (≥1) |
| `page_size` | integer | 20 | Items per page (1-100) |
| `name` | string | null | Filter by name (partial match) |
| `law_type` | string | null | Filter by type (exact match) |
| `jurisdiction` | string | null | Filter by jurisdiction (partial match) |
| `status` | string | null | Filter by status: `raw`, `processed`, `indexed` |

#### **Success Response (200):**
```json
{
  "success": true,
  "message": "Retrieved 15 laws",
  "data": {
    "laws": [
      {
        "id": 1,
        "name": "قانون العمل السعودي",
        "type": "law",
        "jurisdiction": "المملكة العربية السعودية",
        "issuing_authority": "وزارة العمل",
        "issue_date": "2005-04-23",
        "last_update": "2023-02-14",
        "description": "نظام العمل السعودي المعدل",
        "source_url": "https://...",
        "status": "processed",
        "created_at": "2025-10-05T12:00:00Z",
        "updated_at": null
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 15,
      "total_pages": 1
    }
  },
  "errors": []
}
```

---

## 3. Get Law Tree

### `GET /laws/{law_id}/tree`

Retrieve complete hierarchical structure of a law.

#### **Request:**
```http
GET /api/v1/laws/1/tree
Authorization: Bearer {token}
```

#### **Success Response (200):**
```json
{
  "success": true,
  "message": "Law tree retrieved successfully",
  "data": {
    "law_source": {
      "id": 1,
      "name": "قانون العمل السعودي",
      "type": "law",
      "jurisdiction": "المملكة العربية السعودية",
      "issuing_authority": "وزارة العمل",
      "issue_date": "2005-04-23",
      "last_update": "2023-02-14",
      "description": "نظام العمل السعودي المعدل",
      "source_url": "https://...",
      "status": "processed",
      "branches": [
        {
          "id": 1,
          "branch_number": "5",
          "branch_name": "علاقات العمل",
          "description": null,
          "order_index": 0,
          "chapters": [
            {
              "id": 1,
              "chapter_number": "3",
              "chapter_name": "انتهاء عقد العمل",
              "description": null,
              "order_index": 0,
              "articles": [
                {
                  "id": 1,
                  "article_number": "75",
                  "title": "حالات إنهاء العقد",
                  "content": "Full article content...",
                  "keywords": ["إنهاء", "عقد", "عمل"],
                  "order_index": 0,
                  "ai_processed_at": null,
                  "created_at": "2025-10-05T12:00:00Z"
                }
              ],
              "articles_count": 25
            }
          ],
          "chapters_count": 5
        }
      ],
      "branches_count": 6,
      "created_at": "2025-10-05T12:00:00Z",
      "updated_at": null
    }
  },
  "errors": []
}
```

#### **Error Response (404):**
```json
{
  "success": false,
  "message": "Law with ID 999 not found",
  "data": null,
  "errors": []
}
```

---

## 4. Get Law Metadata

### `GET /laws/{law_id}`

Retrieve law metadata only (without hierarchy).

#### **Request:**
```http
GET /api/v1/laws/1
Authorization: Bearer {token}
```

#### **Success Response (200):**
```json
{
  "success": true,
  "message": "Law metadata retrieved successfully",
  "data": {
    "id": 1,
    "name": "قانون العمل السعودي",
    "type": "law",
    "jurisdiction": "المملكة العربية السعودية",
    "issuing_authority": "وزارة العمل",
    "issue_date": "2005-04-23",
    "last_update": "2023-02-14",
    "description": "نظام العمل السعودي المعدل",
    "source_url": "https://...",
    "status": "processed",
    "knowledge_document_id": 5,
    "created_at": "2025-10-05T12:00:00Z",
    "updated_at": null
  },
  "errors": []
}
```

---

## 5. Update Law

### `PUT /laws/{law_id}`

Update law metadata fields.

#### **Request:**
```http
PUT /api/v1/laws/1
Content-Type: multipart/form-data
Authorization: Bearer {token}

Form Data:
  name: "قانون العمل السعودي المعدل"
  description: "Updated description"
  last_update: "2024-01-15"
```

#### **Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | ❌ No | Updated law name |
| `law_type` | enum | ❌ No | Updated type |
| `jurisdiction` | string | ❌ No | Updated jurisdiction |
| `issuing_authority` | string | ❌ No | Updated issuing authority |
| `issue_date` | string | ❌ No | Updated issue date (YYYY-MM-DD) |
| `last_update` | string | ❌ No | Updated last update date |
| `description` | string | ❌ No | Updated description |
| `source_url` | string | ❌ No | Updated source URL |

**Note:** Provide only fields you want to update.

#### **Success Response (200):**
```json
{
  "success": true,
  "message": "Law metadata retrieved successfully",
  "data": {
    "id": 1,
    "name": "قانون العمل السعودي المعدل",
    "type": "law",
    "jurisdiction": "المملكة العربية السعودية",
    "issuing_authority": "وزارة العمل",
    "issue_date": "2005-04-23",
    "last_update": "2024-01-15",
    "description": "Updated description",
    "source_url": "https://...",
    "status": "processed",
    "knowledge_document_id": 5,
    "created_at": "2025-10-05T12:00:00Z",
    "updated_at": "2025-10-05T13:00:00Z"
  },
  "errors": []
}
```

---

## 6. Delete Law

### `DELETE /laws/{law_id}`

Delete law and cascade delete all related data.

#### **Request:**
```http
DELETE /api/v1/laws/1
Authorization: Bearer {token}
```

#### **Cascade Deletes:**
- All `LawBranches`
- All `LawChapters`
- All `LawArticles`
- All linked `KnowledgeChunks`

**Note:** The `KnowledgeDocument` (PDF file) is preserved for audit purposes.

#### **Success Response (200):**
```json
{
  "success": true,
  "message": "Law 'قانون العمل السعودي' deleted successfully",
  "data": {
    "deleted_law_id": 1,
    "deleted_law_name": "قانون العمل السعودي"
  },
  "errors": []
}
```

---

## 7. Reparse Law

### `POST /laws/{law_id}/reparse`

Reparse uploaded PDF and regenerate hierarchy.

#### **Request:**
```http
POST /api/v1/laws/1/reparse
Authorization: Bearer {token}
```

#### **Workflow:**
1. Delete existing branches, chapters, articles, and chunks
2. Re-extract hierarchy from original PDF
3. Recreate all records with updated parsing
4. Update timestamps and status

#### **Use Cases:**
- Improved parsing algorithm
- Fix extraction errors
- Update after model changes

#### **Success Response (200):**
```json
{
  "success": true,
  "message": "Law reparsed successfully",
  "data": null,
  "errors": []
}
```

---

## 8. Analyze Law with AI

### `POST /laws/{law_id}/analyze`

Trigger AI analysis for law articles.

#### **Request:**
```http
POST /api/v1/laws/1/analyze?generate_embeddings=true&extract_keywords=true
Authorization: Bearer {token}
```

#### **Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `generate_embeddings` | boolean | true | Generate AI embeddings for articles |
| `extract_keywords` | boolean | true | Extract keywords using AI |
| `update_existing` | boolean | false | Re-process already analyzed articles |

#### **AI Operations:**
- Generate embeddings for semantic search
- Extract keywords from article content
- Update `ai_processed_at` timestamps
- Store embeddings in article and chunk records

#### **Success Response (200):**
```json
{
  "success": true,
  "message": "AI analysis completed for 145 articles",
  "data": {
    "processed_articles": 145,
    "total_articles": 145
  },
  "errors": []
}
```

---

## 9. Get Law Statistics

### `GET /laws/{law_id}/statistics`

Get comprehensive statistics for a law.

#### **Request:**
```http
GET /api/v1/laws/1/statistics
Authorization: Bearer {token}
```

#### **Success Response (200):**
```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "branches_count": 6,
    "chapters_count": 18,
    "articles_count": 145,
    "chunks_count": 145,
    "verified_chunks": 98,
    "ai_processed_articles": 145
  },
  "errors": []
}
```

---

## Error Handling

All endpoints return errors in standardized format:

```json
{
  "success": false,
  "message": "Human-readable error message",
  "data": null,
  "errors": [
    {
      "field": "field_name",
      "message": "Specific error for this field"
    }
  ]
}
```

### Common HTTP Status Codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid token) |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 500 | Internal Server Error |

---

## Authentication

All endpoints require JWT authentication:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Get Token:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Database Schema Integration

### Entity Relationships:

```
KnowledgeDocument (PDF file)
  └── file_hash (SHA-256 for duplicate detection)
  
LawSource (Law metadata)
  ├── knowledge_document_id → KnowledgeDocument
  ├── status: raw → processed → indexed
  └── LawBranch[] (Branches)
        ├── source_document_id → KnowledgeDocument
        └── LawChapter[] (Chapters)
              ├── source_document_id → KnowledgeDocument
              └── LawArticle[] (Articles)
                    ├── source_document_id → KnowledgeDocument
                    ├── ai_processed_at (timestamp)
                    └── KnowledgeChunk (for search)
                          ├── law_source_id
                          ├── branch_id
                          ├── chapter_id
                          ├── article_id
                          └── verified_by_admin
```

### Key Features:
- ✅ **File Hash Deduplication** - Prevents duplicate uploads
- ✅ **Unified Document Reference** - All entities link to `KnowledgeDocument`
- ✅ **Status Tracking** - Monitor processing stages
- ✅ **AI Processing Audit** - Track when AI analyzed content
- ✅ **Hierarchical Integrity** - Proper parent-child relationships
- ✅ **Cascade Deletes** - Clean up when deleting laws

---

## Example Workflows

### Workflow 1: Upload and Process New Law

```bash
# Step 1: Upload PDF
curl -X POST "http://localhost:8000/api/v1/laws/upload" \
  -H "Authorization: Bearer {token}" \
  -F "law_name=Labor Law" \
  -F "law_type=law" \
  -F "jurisdiction=Saudi Arabia" \
  -F "pdf_file=@labor_law.pdf"

# Response includes full hierarchy tree with law_id

# Step 2: Get statistics
curl -X GET "http://localhost:8000/api/v1/laws/1/statistics" \
  -H "Authorization: Bearer {token}"

# Step 3: Analyze with AI
curl -X POST "http://localhost:8000/api/v1/laws/1/analyze" \
  -H "Authorization: Bearer {token}"
```

### Workflow 2: Update Law Metadata

```bash
# Update law information
curl -X PUT "http://localhost:8000/api/v1/laws/1" \
  -H "Authorization: Bearer {token}" \
  -F "description=Updated description" \
  -F "last_update=2024-01-15"
```

### Workflow 3: Search and Filter Laws

```bash
# Get all processed laws
curl -X GET "http://localhost:8000/api/v1/laws/?status=processed&page=1&page_size=10" \
  -H "Authorization: Bearer {token}"

# Search by name
curl -X GET "http://localhost:8000/api/v1/laws/?name=عمل" \
  -H "Authorization: Bearer {token}"
```

---

## Testing

### Using cURL:

```bash
# Upload law
curl -X POST "http://localhost:8000/api/v1/laws/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "law_name=Test Law" \
  -F "law_type=law" \
  -F "jurisdiction=Test" \
  -F "pdf_file=@test.pdf"

# List laws
curl -X GET "http://localhost:8000/api/v1/laws/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get tree
curl -X GET "http://localhost:8000/api/v1/laws/1/tree" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using Python Requests:

```python
import requests

API_URL = "http://localhost:8000/api/v1/laws"
TOKEN = "your_jwt_token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Upload law
files = {"pdf_file": open("labor_law.pdf", "rb")}
data = {
    "law_name": "Labor Law",
    "law_type": "law",
    "jurisdiction": "Saudi Arabia"
}
response = requests.post(f"{API_URL}/upload", headers=headers, files=files, data=data)
print(response.json())

# Get tree
response = requests.get(f"{API_URL}/1/tree", headers=headers)
print(response.json())
```

---

## Rate Limiting

- **Upload:** 10 requests per minute
- **List/Get:** 100 requests per minute
- **AI Analysis:** 5 requests per minute

---

## Support

For issues or questions:
- API Documentation: `/docs` (Swagger UI)
- ReDoc: `/redoc`
- Contact: support@example.com

---

**Version:** 1.0.0  
**Last Updated:** October 5, 2025
