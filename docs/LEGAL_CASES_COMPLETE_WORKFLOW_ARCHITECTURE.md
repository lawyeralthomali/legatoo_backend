# 📋 Legal Cases Router - Complete Workflow & Architecture Analysis

## 📌 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Complete Code Structure](#complete-code-structure)
4. [Workflow Diagrams](#workflow-diagrams)
5. [Endpoint Details](#endpoint-details)
6. [Data Flow](#data-flow)
7. [Database Models](#database-models)
8. [Services Layer](#services-layer)
9. [Repository Layer](#repository-layer)
10. [Error Handling](#error-handling)
11. [Authentication & Authorization](#authentication--authorization)

---

## 🎯 Overview

The Legal Cases system is a comprehensive platform for ingesting, managing, and retrieving historical legal case documents. It follows **Clean Architecture** principles with clear separation between:

- **Router Layer** (API endpoints)
- **Service Layer** (Business logic)
- **Repository Layer** (Data access)
- **Model Layer** (Database entities)

### Key Features

✅ **File Upload**: PDF, DOCX, TXT support with Arabic text processing  
✅ **JSON Upload**: Structured case data ingestion  
✅ **CRUD Operations**: Full management of legal cases  
✅ **Advanced Search**: Filter by jurisdiction, type, court level, etc.  
✅ **Section Management**: Structured case sections (summary, facts, arguments, ruling, legal_basis)  
✅ **Duplicate Detection**: SHA-256 hash-based file deduplication  

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT REQUEST                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION LAYER                      │
│                   (get_current_user)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      ROUTER LAYER                            │
│              (legal_cases_router.py)                         │
│                                                               │
│  Endpoints:                                                   │
│  • POST   /upload          - Upload case files               │
│  • POST   /upload-json     - Upload JSON structure           │
│  • GET    /                - List cases                      │
│  • GET    /{id}            - Get case details                │
│  • PUT    /{id}            - Update case                     │
│  • DELETE /{id}            - Delete case                     │
│  • GET    /{id}/sections   - Get case sections               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                            │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │     LegalCaseIngestionService                         │  │
│  │  • File upload & extraction                           │  │
│  │  • Text processing (Arabic)                           │  │
│  │  • Section segmentation                               │  │
│  │  • Database storage                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │     LegalCaseService                                  │  │
│  │  • CRUD operations                                    │  │
│  │  • JSON structure upload                              │  │
│  │  • Search & filtering                                 │  │
│  │  • Business logic                                     │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   REPOSITORY LAYER                           │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │     LegalCaseRepository                               │  │
│  │  • create_legal_case()                                │  │
│  │  • get_case_by_id()                                   │  │
│  │  • get_cases()                                        │  │
│  │  • search_cases()                                     │  │
│  │  • update_legal_case()                                │  │
│  │  • delete_legal_case()                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │     CaseSectionRepository                             │  │
│  │  • create_case_section()                              │  │
│  │  • get_sections_by_case()                             │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      MODEL LAYER                             │
│                (Database Entities)                           │
│                                                               │
│  • KnowledgeDocument                                          │
│  • LegalCase                                                  │
│  • CaseSection                                                │
│  • KnowledgeChunk                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Complete Code Structure

```
app/
├── routes/
│   └── legal_cases_router.py       # API endpoints
│
├── services/
│   ├── legal_case_service.py       # CRUD & JSON upload logic
│   └── legal_case_ingestion_service.py  # File processing & ingestion
│
├── repositories/
│   └── legal_knowledge_repository.py
│       ├── LegalCaseRepository     # Data access for cases
│       └── CaseSectionRepository   # Data access for sections
│
├── models/
│   └── legal_knowledge.py
│       ├── KnowledgeDocument       # File metadata
│       ├── LegalCase               # Case entity
│       ├── CaseSection             # Section entity
│       └── KnowledgeChunk          # Text chunks
│
├── schemas/
│   └── response.py
│       ├── ApiResponse             # Unified response model
│       ├── ErrorDetail             # Error structure
│       ├── create_success_response()
│       └── create_error_response()
│
└── utils/
    └── auth.py
        └── get_current_user()      # JWT authentication
```

---

## 🔄 Workflow Diagrams

### 1️⃣ File Upload Workflow (`POST /upload`)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CLIENT UPLOADS FILE (PDF/DOCX/TXT)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. ROUTER VALIDATION                                          │
│    • Validate file type (pdf, docx, txt)                     │
│    • Check file is not empty                                 │
│    • Validate required metadata (title)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. INGESTION SERVICE: save_uploaded_case_file()              │
│    • Calculate SHA-256 hash                                  │
│    • Check for duplicate (file_hash)                         │
│    • Save file to: uploads/legal_cases/                      │
│    • Create KnowledgeDocument record                         │
│      - title, category='case', file_path, file_hash          │
│      - status='raw', uploaded_by, uploaded_at                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. TEXT EXTRACTION: extract_text()                           │
│    • PDF: PyMuPDF with dict extraction                       │
│      - Extract blocks → lines → spans                        │
│      - Apply Arabic text fixing:                             │
│        * Clean Unicode artifacts                             │
│        * Normalize fragmented text                           │
│        * Arabic reshaping                                    │
│        * BiDi algorithm for RTL                              │
│    • DOCX: python-docx paragraph extraction                  │
│    • TXT: UTF-8/Windows-1256/ISO-8859-1 decoding             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. SECTION SEGMENTATION: split_case_sections()               │
│    • Scan text for Arabic keywords:                          │
│      - ملخص/الملخص → summary                                 │
│      - الوقائع/وقائع القضية → facts                          │
│      - الحجج/حجج الأطراف → arguments                         │
│      - الحكم/منطوق الحكم → ruling                            │
│      - الأساس القانوني/المادة → legal_basis                  │
│    • Extract content between markers                         │
│    • If no markers: entire text → summary                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. DATABASE STORAGE: save_case_with_sections()               │
│    • Parse decision_date (YYYY-MM-DD)                        │
│    • Create LegalCase record:                                │
│      - case_number, title, description                       │
│      - jurisdiction, court_name, decision_date               │
│      - case_type, court_level                                │
│      - document_id, status='raw'                             │
│    • Create CaseSection records:                             │
│      - case_id, section_type, content                        │
│      - One record per non-empty section                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 7. UPDATE STATUS                                              │
│    • KnowledgeDocument.status = 'processed'                  │
│    • LegalCase.status = 'processed'                          │
│    • Commit transaction                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 8. RETURN SUCCESS RESPONSE                                    │
│    {                                                          │
│      "success": true,                                         │
│      "message": "Legal case uploaded successfully",           │
│      "data": {                                                │
│        "knowledge_document_id": 123,                          │
│        "legal_case_id": 456,                                  │
│        "case_number": "123/2024",                             │
│        "title": "قضية عمالية...",                            │
│        "sections_found": ["summary", "facts", "ruling"],      │
│        "sections_count": 3                                    │
│      },                                                       │
│      "errors": []                                             │
│    }                                                          │
└──────────────────────────────────────────────────────────────┘
```

### 2️⃣ JSON Upload Workflow (`POST /upload-json`)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CLIENT UPLOADS JSON FILE                                  │
│    {                                                          │
│      "legal_cases": [{                                        │
│        "case_number": "123/2024",                             │
│        "title": "قضية عمالية",                               │
│        "sections": [                                          │
│          {"section_type": "summary", "content": "..."},       │
│          {"section_type": "facts", "content": "..."}          │
│        ]                                                      │
│      }]                                                       │
│    }                                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. ROUTER VALIDATION                                          │
│    • Check file extension is .json                           │
│    • Parse JSON content                                      │
│    • Validate "legal_cases" array exists                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. SERVICE: upload_json_case_structure()                     │
│    For each case in legal_cases:                             │
│                                                               │
│    A. Generate unique hash (SHA-256 of JSON content)         │
│                                                               │
│    B. Create KnowledgeDocument                               │
│       • title = "JSON Upload: {case_title}"                  │
│       • category = "legal_case"                              │
│       • file_path = "json_upload_case_{hash}.json"           │
│       • file_hash = "{hash}_{index}"                         │
│       • status = "processed"                                 │
│       • document_metadata = processing_report                │
│                                                               │
│    C. Create LegalCase                                       │
│       • Parse decision_date (multiple formats supported)     │
│       • Link to document_id                                  │
│       • status = "processed"                                 │
│                                                               │
│    D. Create CaseSection (for each section)                  │
│       • Validate section_type in allowed list                │
│       • Link to case_id                                      │
│                                                               │
│    E. Create KnowledgeChunk (for each section)               │
│       • document_id, chunk_index, content                    │
│       • case_id (link to legal case)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. COMMIT TRANSACTION                                         │
│    • Commit all created records                              │
│    • Return statistics                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. RETURN SUCCESS RESPONSE                                    │
│    {                                                          │
│      "success": true,                                         │
│      "message": "Successfully processed 1 legal case(s)...",  │
│      "data": {                                                │
│        "cases": [                                             │
│          {                                                    │
│            "id": 456,                                         │
│            "case_number": "123/2024",                         │
│            "title": "قضية عمالية"                            │
│          }                                                    │
│        ],                                                     │
│        "statistics": {                                        │
│          "total_cases": 1,                                    │
│          "total_sections": 3,                                 │
│          "processing_report": {...}                           │
│        }                                                      │
│      },                                                       │
│      "errors": []                                             │
│    }                                                          │
└──────────────────────────────────────────────────────────────┘
```

### 3️⃣ Get Case Details Workflow (`GET /{case_id}`)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CLIENT REQUEST: GET /api/v1/legal-cases/123              │
│    Query params: include_sections=true                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. AUTHENTICATION                                             │
│    • Verify JWT token                                        │
│    • Extract current_user                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. SERVICE: get_legal_case()                                 │
│    • Call repository.get_case_by_id(123)                     │
│    • If not found: return error response                     │
│    • Format case data (convert dates to ISO)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. IF include_sections=true                                  │
│    • Call repository.get_sections_by_case(123)               │
│    • Format sections data                                    │
│    • Add to case_data['sections']                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. RETURN SUCCESS RESPONSE                                    │
│    {                                                          │
│      "success": true,                                         │
│      "message": "Legal case retrieved successfully",          │
│      "data": {                                                │
│        "id": 123,                                             │
│        "case_number": "123/2024",                             │
│        "title": "قضية عمالية",                               │
│        "description": "...",                                  │
│        "jurisdiction": "الرياض",                              │
│        "court_name": "المحكمة العمالية",                      │
│        "decision_date": "2024-01-15",                         │
│        "case_type": "عمل",                                    │
│        "court_level": "ابتدائي",                              │
│        "status": "processed",                                 │
│        "sections": [                                          │
│          {"id": 1, "section_type": "summary", "content": ...},│
│          {"id": 2, "section_type": "facts", "content": ...}   │
│        ],                                                     │
│        "sections_count": 2                                    │
│      },                                                       │
│      "errors": []                                             │
│    }                                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔌 Endpoint Details

### 1. Upload Legal Case File

**Endpoint**: `POST /api/v1/legal-cases/upload`

**Authentication**: Required (JWT)

**Request**:
```
Content-Type: multipart/form-data

Fields:
- file: UploadFile (PDF/DOCX/TXT) [Required]
- title: string [Required]
- case_number: string [Optional]
- description: string [Optional]
- jurisdiction: string [Optional]
- court_name: string [Optional]
- decision_date: string (YYYY-MM-DD) [Optional]
- case_type: string [Optional] (مدني, جنائي, تجاري, عمل, إداري)
- court_level: string [Optional] (ابتدائي, استئناف, تمييز, عالي)
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Legal case uploaded successfully",
  "data": {
    "knowledge_document_id": 123,
    "legal_case_id": 456,
    "case_number": "123/2024",
    "title": "قضية عمالية - إنهاء خدمات",
    "file_path": "uploads/legal_cases/20240115_abc123.pdf",
    "file_hash": "abc123...",
    "text_length": 15000,
    "sections_found": ["summary", "facts", "ruling"],
    "sections_count": 3
  },
  "errors": []
}
```

**Error Responses**:

- **400 Bad Request**: Invalid file format or empty file
```json
{
  "success": false,
  "message": "Invalid file format. Only PDF, DOCX, and TXT are supported.",
  "data": null,
  "errors": [
    {"field": "file", "message": "Only PDF, DOCX, and TXT files are supported"}
  ]
}
```

- **422 Unprocessable Entity**: Ingestion failed
```json
{
  "success": false,
  "message": "Extracted text is too short (50 chars). Possible causes: ...",
  "data": null,
  "errors": [
    {"field": null, "message": "Extracted text is too short..."}
  ]
}
```

- **500 Internal Server Error**: Unexpected error
```json
{
  "success": false,
  "message": "Failed to upload legal case: {error_message}",
  "data": null,
  "errors": [
    {"field": null, "message": "{error_message}"}
  ]
}
```

---

### 2. Upload JSON Case Structure

**Endpoint**: `POST /api/v1/legal-cases/upload-json`

**Authentication**: Required (JWT)

**Request**:
```
Content-Type: multipart/form-data

Fields:
- json_file: UploadFile (.json) [Required]
```

**JSON File Format**:
```json
{
  "legal_cases": [
    {
      "case_number": "123/2024",
      "title": "قضية عمالية - إنهاء خدمات",
      "description": "نزاع حول إنهاء خدمات عامل بدون مبرر",
      "jurisdiction": "الرياض",
      "court_name": "المحكمة العمالية بالرياض",
      "decision_date": "2024-01-15",
      "case_type": "عمل",
      "court_level": "ابتدائي",
      "sections": [
        {
          "section_type": "summary",
          "content": "ملخص القضية: نزاع بين عامل وصاحب عمل..."
        },
        {
          "section_type": "facts",
          "content": "وقائع القضية: تقدم العامل بشكوى..."
        },
        {
          "section_type": "arguments",
          "content": "حجج الأطراف: ادعى العامل أن..."
        },
        {
          "section_type": "ruling",
          "content": "الحكم: حكمت المحكمة بإلزام صاحب العمل..."
        },
        {
          "section_type": "legal_basis",
          "content": "الأساس القانوني: استندت المحكمة إلى المادة 74..."
        }
      ]
    }
  ],
  "processing_report": {
    "total_cases": 1,
    "warnings": [],
    "errors": [],
    "suggestions": ["تحقق من اكتمال البيانات"]
  }
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "✅ Successfully processed JSON case structure: Successfully processed 1 legal case(s) with 5 section(s)",
  "data": {
    "cases": [
      {
        "id": 456,
        "case_number": "123/2024",
        "title": "قضية عمالية - إنهاء خدمات"
      }
    ],
    "statistics": {
      "total_cases": 1,
      "total_sections": 5,
      "processing_report": {...}
    }
  },
  "errors": []
}
```

**Error Responses**:

- **400 Bad Request**: Invalid JSON file
```json
{
  "success": false,
  "message": "Invalid JSON format: Expecting value: line 1 column 1 (char 0)",
  "data": null,
  "errors": []
}
```

- **400 Bad Request**: Missing legal_cases array
```json
{
  "success": false,
  "message": "Invalid JSON structure. Missing 'legal_cases' array",
  "data": null,
  "errors": []
}
```

---

### 3. List Legal Cases

**Endpoint**: `GET /api/v1/legal-cases/`

**Authentication**: Required (JWT)

**Query Parameters**:
```
- skip: int = 0
- limit: int = 50
- jurisdiction: string [Optional]
- case_type: string [Optional]
- court_level: string [Optional]
- status: string [Optional] (raw, processed, indexed)
- search: string [Optional]
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Retrieved 10 legal cases",
  "data": {
    "cases": [
      {
        "id": 1,
        "case_number": "123/2024",
        "title": "قضية عمالية - إنهاء خدمات",
        "description": "نزاع حول إنهاء خدمات عامل",
        "jurisdiction": "الرياض",
        "court_name": "المحكمة العمالية بالرياض",
        "decision_date": "2024-01-15",
        "case_type": "عمل",
        "court_level": "ابتدائي",
        "status": "processed",
        "document_id": 123,
        "created_at": "2024-01-15T10:30:00"
      }
    ],
    "total": 10,
    "skip": 0,
    "limit": 50
  },
  "errors": []
}
```

---

### 4. Get Case Details

**Endpoint**: `GET /api/v1/legal-cases/{case_id}`

**Authentication**: Required (JWT)

**Query Parameters**:
```
- include_sections: bool = true
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Legal case retrieved successfully",
  "data": {
    "id": 1,
    "case_number": "123/2024",
    "title": "قضية عمالية - إنهاء خدمات",
    "description": "نزاع حول إنهاء خدمات عامل",
    "jurisdiction": "الرياض",
    "court_name": "المحكمة العمالية بالرياض",
    "decision_date": "2024-01-15",
    "case_type": "عمل",
    "court_level": "ابتدائي",
    "document_id": 123,
    "status": "processed",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:35:00",
    "sections": [
      {
        "id": 1,
        "section_type": "summary",
        "content": "ملخص القضية...",
        "created_at": "2024-01-15T10:30:00"
      },
      {
        "id": 2,
        "section_type": "facts",
        "content": "وقائع القضية...",
        "created_at": "2024-01-15T10:30:00"
      }
    ],
    "sections_count": 2
  },
  "errors": []
}
```

**Error Response** (404):
```json
{
  "success": false,
  "message": "Legal case with ID 999 not found",
  "data": null,
  "errors": [
    {"field": "case_id", "message": "Case not found"}
  ]
}
```

---

### 5. Update Legal Case

**Endpoint**: `PUT /api/v1/legal-cases/{case_id}`

**Authentication**: Required (JWT)

**Request**:
```
Content-Type: multipart/form-data

Fields (all optional):
- case_number: string
- title: string
- description: string
- jurisdiction: string
- court_name: string
- decision_date: string (YYYY-MM-DD)
- case_type: string
- court_level: string
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Legal case updated successfully",
  "data": {
    "id": 1,
    "case_number": "123/2024",
    "title": "قضية عمالية محدثة",
    "updated_at": "2024-01-15T11:00:00"
  },
  "errors": []
}
```

---

### 6. Delete Legal Case

**Endpoint**: `DELETE /api/v1/legal-cases/{case_id}`

**Authentication**: Required (JWT)

**Success Response** (200):
```json
{
  "success": true,
  "message": "Legal case 1 deleted successfully",
  "data": {
    "deleted_case_id": 1
  },
  "errors": []
}
```

**Note**: This deletes the LegalCase and all its CaseSections (cascade delete). The KnowledgeDocument is NOT deleted, only the link is removed.

---

### 7. Get Case Sections

**Endpoint**: `GET /api/v1/legal-cases/{case_id}/sections`

**Authentication**: Required (JWT)

**Query Parameters**:
```
- section_type: string [Optional] (summary, facts, arguments, ruling, legal_basis)
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Retrieved 3 sections",
  "data": {
    "sections": [
      {
        "id": 1,
        "case_id": 1,
        "section_type": "summary",
        "content": "ملخص القضية...",
        "created_at": "2024-01-15T10:30:00"
      },
      {
        "id": 2,
        "case_id": 1,
        "section_type": "facts",
        "content": "وقائع القضية...",
        "created_at": "2024-01-15T10:30:00"
      },
      {
        "id": 3,
        "case_id": 1,
        "section_type": "ruling",
        "content": "الحكم...",
        "created_at": "2024-01-15T10:30:00"
      }
    ],
    "count": 3
  },
  "errors": []
}
```

---

## 💾 Database Models

### 1. KnowledgeDocument

**Purpose**: Stores metadata about uploaded files

**Table**: `knowledge_documents`

```python
class KnowledgeDocument(Base):
    id: int [PK]
    title: str [Required]
    category: str [Required] # 'law', 'case', 'contract', etc.
    file_path: str [Optional]
    file_hash: str [Unique, Indexed] # SHA-256 hash
    source_type: str [Required] # 'uploaded', 'web_scraped', 'api_import'
    status: str [Default: 'raw'] # 'raw', 'processed', 'indexed'
    uploaded_by: int [FK → users.id]
    uploaded_at: DateTime [Auto]
    processed_at: DateTime [Optional]
    document_metadata: JSON [Optional]
    
    # Relationships
    chunks: List[KnowledgeChunk]
    analysis_results: List[AnalysisResult]
```

**Indexes**:
- `file_hash` (unique)
- `category`, `status`

---

### 2. LegalCase

**Purpose**: Stores legal case metadata

**Table**: `legal_cases`

```python
class LegalCase(Base):
    id: int [PK]
    case_number: str [Indexed]
    title: str [Required]
    description: str [Optional]
    jurisdiction: str [Indexed] # "الرياض", "جدة", etc.
    court_name: str [Optional]
    decision_date: Date [Indexed]
    case_type: str [Check Constraint]
        # 'مدني', 'جنائي', 'تجاري', 'عمل', 'إداري'
    court_level: str [Check Constraint]
        # 'ابتدائي', 'استئناف', 'تمييز', 'عالي'
    document_id: int [FK → knowledge_documents.id] [Optional]
    status: str [Default: 'raw'] # 'raw', 'processed', 'indexed'
    created_at: DateTime [Auto]
    updated_at: DateTime [Auto on update]
    
    # Relationships
    document: KnowledgeDocument
    sections: List[CaseSection] [Cascade delete]
    chunks: List[KnowledgeChunk]
```

**Indexes**:
- `case_number`
- `jurisdiction`, `decision_date`
- `status`

**Check Constraints**:
- `case_type IN ('مدني', 'جنائي', 'تجاري', 'عمل', 'إداري')`
- `court_level IN ('ابتدائي', 'استئناف', 'تمييز', 'عالي')`
- `status IN ('raw', 'processed', 'indexed')`

---

### 3. CaseSection

**Purpose**: Stores structured sections of legal cases

**Table**: `case_sections`

```python
class CaseSection(Base):
    id: int [PK]
    case_id: int [FK → legal_cases.id] [Required, Indexed]
    section_type: str [Check Constraint]
        # 'summary', 'facts', 'arguments', 'ruling', 'legal_basis'
    content: str [Required]
    embedding: str [Optional] # JSON-encoded vector
    ai_processed_at: DateTime [Optional]
    created_at: DateTime [Auto]
    
    # Relationships
    case: LegalCase
```

**Indexes**:
- `case_id`
- `section_type`

**Check Constraints**:
- `section_type IN ('summary', 'facts', 'arguments', 'ruling', 'legal_basis')`

---

### 4. KnowledgeChunk

**Purpose**: Stores text chunks for embedding and search

**Table**: `knowledge_chunks`

```python
class KnowledgeChunk(Base):
    id: int [PK]
    document_id: int [FK → knowledge_documents.id] [Required, Indexed]
    chunk_index: int [Required]
    content: str [Required]
    tokens_count: int [Optional]
    embedding: str [Optional] # JSON-encoded vector
    verified_by_admin: bool [Default: False, Indexed]
    
    # Foreign keys for linking
    law_source_id: int [FK → law_sources.id] [Optional]
    branch_id: int [FK → law_branches.id] [Optional]
    chapter_id: int [FK → law_chapters.id] [Optional]
    article_id: int [FK → law_articles.id] [Optional]
    case_id: int [FK → legal_cases.id] [Optional]
    term_id: int [FK → legal_terms.id] [Optional]
    
    created_at: DateTime [Auto]
    
    # Relationships
    document: KnowledgeDocument
    law_source: LawSource
    branch: LawBranch
    chapter: LawChapter
    article: LawArticle
    legal_case: LegalCase
    legal_term: LegalTerm
```

**Indexes**:
- `document_id`
- `law_source_id`, `branch_id`, `chapter_id`, `article_id`, `case_id`
- `tokens_count`
- `verified_by_admin`

---

## 🔧 Services Layer

### LegalCaseIngestionService

**File**: `app/services/legal_case_ingestion_service.py`

**Purpose**: Complete pipeline for ingesting legal cases from files

**Key Methods**:

#### `ingest_legal_case(file_content, filename, case_metadata, uploaded_by)`

Complete ingestion pipeline:
1. Save file → calculate hash → check duplicates
2. Extract text (PDF/DOCX/TXT)
3. Apply Arabic text processing
4. Segment into sections
5. Store in database
6. Update status

**Returns**: Dict with success status and ingestion results

---

#### `save_uploaded_case_file(file_content, filename, uploaded_by)`

- Calculate SHA-256 hash of file content
- Check for duplicate files (by hash)
- Save file to `uploads/legal_cases/`
- Create `KnowledgeDocument` record
- **Raises**: `ValueError` if duplicate detected

---

#### `extract_text(file_path)`

Extract text based on file type:
- **PDF**: PyMuPDF with dict extraction + Arabic text fixing
- **DOCX**: python-docx paragraph extraction
- **TXT**: UTF-8/Windows-1256/ISO-8859-1 decoding

---

#### `_extract_pdf_text(file_path)`

Advanced PDF extraction:
1. Open PDF with PyMuPDF (fitz)
2. For each page:
   - Extract with `get_text("dict")`
   - Process blocks → lines → spans
   - Apply Arabic text fixing to each line
3. Return full text with page separators

---

#### `_fix_arabic_text(text)`

Comprehensive Arabic text fixing:
1. Clean Unicode artifacts (fragmented characters)
2. Normalize fragmented text (merge broken letters)
3. Apply Arabic reshaping (connect letters properly)
4. Apply BiDi algorithm (RTL display)

**Arabic Processing Steps**:

**Step 1: Clean Artifacts**
```python
artifacts_map = {
    'ﻢ': 'م', 'ﻪ': 'ه', 'ﻆ': 'ظ',
    'ﺍ': 'ا', 'ﺕ': 'ت', 'ﺏ': 'ب',
    # ... 100+ mappings
}
```

**Step 2: Normalize Fragmented Text**
- Detect single Arabic characters
- Merge them into complete words
- Preserve numbers and English

**Step 3: Arabic Reshaping**
```python
import arabic_reshaper
reshaped = arabic_reshaper.reshape(word)
```

**Step 4: BiDi Algorithm**
```python
from bidi.algorithm import get_display
fixed_text = get_display(reshaped_text)
```

---

#### `split_case_sections(text)`

Section segmentation using regex patterns:

**Patterns by Section Type**:

```python
section_patterns = {
    'summary': [
        r'الحمدلله\s+والصلاة\s+والسلام',
        r'ملخص\s+القضية',
        r'ملخص\s+الدعوى',
        r'نبذة', r'موجز'
    ],
    'facts': [
        r'تتحصل\s+وقائع',
        r'ما\s+ورد\s+في\s+صحيفة\s+الدعوى',
        r'وقائع\s+القضية',
        r'الوقائع'
    ],
    'arguments': [
        r'تقرير\s+المحامي',
        r'حجج\s+الأطراف',
        r'المرافعات',
        r'الدفوع'
    ],
    'ruling': [
        r'منطوق\s+الحكم',
        r'حكمت\s+المحكمة',
        r'قررت\s+المحكمة',
        r'الحكم'
    ],
    'legal_basis': [
        r'المادة\s+\d+',
        r'الأساس\s+القانوني',
        r'السند\s+القانوني',
        r'الحيثيات'
    ]
}
```

**Algorithm**:
1. Find all section markers with positions
2. Sort markers by position
3. Extract content between markers
4. If no markers found: put entire text in summary

**Returns**: Dict with section types as keys

---

#### `save_case_with_sections(case_metadata, sections, document_id)`

1. Parse `decision_date` (string → date)
2. Create `LegalCase` record
3. Create `CaseSection` records for non-empty sections
4. Return created `LegalCase` instance

---

### LegalCaseService

**File**: `app/services/legal_case_service.py`

**Purpose**: Business logic for CRUD operations and JSON upload

**Key Methods**:

#### `list_legal_cases(skip, limit, filters...)`

- Apply filters (jurisdiction, case_type, court_level, status)
- If search provided: call `repository.search_cases()`
- Otherwise: call `repository.get_cases()` with filters
- Format response with pagination metadata

---

#### `get_legal_case(case_id, include_sections)`

- Get case by ID from repository
- If not found: return error response
- Format case data (convert dates to ISO)
- If `include_sections=True`: fetch and format sections
- Return success response

---

#### `update_legal_case(case_id, **updates)`

- Build updates dictionary (only non-None values)
- Parse `decision_date` if provided
- Validate date format
- Call repository to update
- Return success/error response

---

#### `delete_legal_case(case_id)`

- Call repository to delete
- If not found: return error response
- Return success with deleted case ID

---

#### `get_case_sections(case_id, section_type)`

- Get sections from repository
- Apply `section_type` filter if provided
- Format sections data
- Return success with sections array

---

#### `upload_json_case_structure(json_data, uploaded_by)`

**Complete JSON upload workflow**:

```python
async def upload_json_case_structure(json_data, uploaded_by):
    # 1. Extract legal_cases array
    legal_cases = json_data.get("legal_cases", [])
    
    # 2. Generate unique hash for JSON
    json_content = json.dumps(json_data, sort_keys=True)
    unique_hash = hashlib.sha256(json_content.encode()).hexdigest()
    
    # 3. For each case:
    for case_data in legal_cases:
        # A. Create KnowledgeDocument
        knowledge_doc = KnowledgeDocument(
            title=f"JSON Upload: {case_data['title']}",
            category="legal_case",
            file_path=f"json_upload_case_{hash[:8]}.json",
            file_hash=f"{hash}_{index}",
            status="processed"
        )
        
        # B. Create LegalCase
        legal_case = LegalCase(
            document_id=knowledge_doc.id,
            case_number=case_data.get("case_number"),
            title=case_data.get("title"),
            # ... other fields
            status="processed"
        )
        
        # C. Create CaseSection for each section
        for section_data in case_data.get("sections", []):
            case_section = CaseSection(
                case_id=legal_case.id,
                section_type=section_data["section_type"],
                content=section_data["content"]
            )
            
        # D. Create KnowledgeChunk for each section
            chunk = KnowledgeChunk(
                document_id=knowledge_doc.id,
                chunk_index=chunk_index,
                content=content,
                case_id=legal_case.id
            )
    
    # 4. Commit transaction
    await self.db.commit()
    
    # 5. Return success with statistics
    return {
        "success": True,
        "data": {
            "cases": [...],
            "statistics": {
                "total_cases": ...,
                "total_sections": ...
            }
        }
    }
```

---

## 📊 Repository Layer

### LegalCaseRepository

**File**: `app/repositories/legal_knowledge_repository.py`

**Purpose**: Data access layer for legal cases

**Key Methods**:

#### `create_legal_case(**kwargs) → LegalCase`
- Create new LegalCase record
- Commit to database
- Return created instance

---

#### `get_case_by_id(case_id) → Optional[LegalCase]`
- Query with `selectinload(LegalCase.sections)`
- Return case with sections preloaded

---

#### `get_cases(skip, limit, filters...) → Tuple[List[LegalCase], int]`
- Build query with filters
- Get total count
- Apply pagination (offset, limit)
- Order by `decision_date DESC`
- Return (cases, total)

---

#### `search_cases(search_term, limit) → List[LegalCase]`
- Search in: title, description, case_number, case_type, court_level, case_outcome
- Use `ILIKE` for case-insensitive search
- Limit results

---

#### `update_legal_case(case_id, **updates) → Optional[LegalCase]`
- Get case by ID
- Update only provided fields
- Commit changes
- Return updated case

---

#### `delete_legal_case(case_id) → bool`
- Get case by ID
- Delete (cascade to sections)
- Commit
- Return success status

---

### CaseSectionRepository

**File**: `app/repositories/legal_knowledge_repository.py`

**Purpose**: Data access layer for case sections

**Key Methods**:

#### `create_case_section(case_id, content, section_type, embedding) → CaseSection`
- Create new CaseSection record
- Encode embedding as JSON if provided
- Commit to database
- Return created instance

---

#### `get_sections_by_case(case_id, section_type) → List[CaseSection]`
- Query sections for case ID
- Apply `section_type` filter if provided
- Order by ID
- Return list of sections

---

## ⚠️ Error Handling

### Error Response Format

All errors follow the unified response structure:

```json
{
  "success": false,
  "message": "Human-readable error message",
  "data": null,
  "errors": [
    {
      "field": "field_name or null",
      "message": "Specific error description"
    }
  ]
}
```

### Error Categories

#### 1. **Validation Errors** (400 Bad Request)

**Triggers**:
- Invalid file type
- Empty file
- Missing required fields
- Invalid enum values (case_type, court_level, section_type)

**Example**:
```json
{
  "success": false,
  "message": "Invalid file format. Only PDF, DOCX, and TXT are supported.",
  "data": null,
  "errors": [
    {
      "field": "file",
      "message": "Only PDF, DOCX, and TXT files are supported"
    }
  ]
}
```

---

#### 2. **Not Found Errors** (404 Not Found)

**Triggers**:
- Case ID doesn't exist
- Resource not found

**Example**:
```json
{
  "success": false,
  "message": "Legal case with ID 999 not found",
  "data": null,
  "errors": [
    {
      "field": "case_id",
      "message": "Case not found"
    }
  ]
}
```

---

#### 3. **Processing Errors** (422 Unprocessable Entity)

**Triggers**:
- Text extraction failed
- Extracted text too short
- JSON parsing failed
- Invalid JSON structure

**Example**:
```json
{
  "success": false,
  "message": "Extracted text is too short (50 chars). Possible causes: PDF is image-based, file corrupted, etc.",
  "data": null,
  "errors": [
    {
      "field": null,
      "message": "Extracted text is too short (50 chars)..."
    }
  ]
}
```

---

#### 4. **Duplicate Errors** (400 Bad Request)

**Triggers**:
- File with same hash already exists

**Example**:
```json
{
  "success": false,
  "message": "Duplicate file detected. Document already exists: Case Title (ID: 123)",
  "data": null,
  "errors": [
    {
      "field": "file",
      "message": "Duplicate file detected..."
    }
  ]
}
```

---

#### 5. **Server Errors** (500 Internal Server Error)

**Triggers**:
- Unexpected exceptions
- Database errors
- File system errors

**Example**:
```json
{
  "success": false,
  "message": "Failed to upload legal case: Database connection error",
  "data": null,
  "errors": [
    {
      "field": null,
      "message": "Database connection error"
    }
  ]
}
```

### Error Handling Flow

```python
try:
    # Main processing logic
    result = await service.process()
    return success_response(result)
    
except HTTPException:
    # Re-raise HTTPException as-is
    raise
    
except ValueError as e:
    # Validation errors
    raise HTTPException(
        status_code=400,
        detail={
            "success": False,
            "message": str(e),
            "data": None,
            "errors": [{"field": None, "message": str(e)}]
        }
    )
    
except Exception as e:
    # Log unexpected errors
    logger.exception("Unexpected error")
    
    # Rollback transaction
    await db.rollback()
    
    # Clean up resources (e.g., delete uploaded file)
    cleanup_resources()
    
    # Return 500 error
    raise HTTPException(
        status_code=500,
        detail={
            "success": False,
            "message": f"Failed to process: {str(e)}",
            "data": None,
            "errors": [{"field": None, "message": str(e)}]
        }
    )
```

---

## 🔐 Authentication & Authorization

### Authentication Middleware

**Function**: `get_current_user()`

**File**: `app/utils/auth.py`

**Flow**:
1. Extract JWT token from Authorization header
2. Verify token signature
3. Decode token payload
4. Extract user information (sub, email, role, etc.)
5. Return `User` object

**Usage in Router**:
```python
@router.post("/upload")
async def upload_legal_case(
    file: UploadFile = File(...),
    # ... other params
    current_user = Depends(get_current_user)  # Authentication
):
    # current_user.sub = user ID
    # current_user.email = user email
    # current_user.role = user role
```

### Authorization

Currently, all authenticated users can:
- Upload cases
- View cases
- Update cases
- Delete cases

**Future Enhancement**: Role-based access control (RBAC)
- `admin`: Full access
- `legal_expert`: Upload, update, view
- `viewer`: View only

---

## 📈 Data Flow Summary

### Upload File Flow

```
Client
  ↓ (HTTP POST with file)
Router (Validation)
  ↓
LegalCaseIngestionService
  ↓
  ├→ save_uploaded_case_file()
  │   ├→ Calculate hash
  │   ├→ Check duplicates
  │   ├→ Save to uploads/
  │   └→ Create KnowledgeDocument
  ↓
  ├→ extract_text()
  │   ├→ PDF: PyMuPDF + Arabic fixing
  │   ├→ DOCX: python-docx
  │   └→ TXT: UTF-8 decoding
  ↓
  ├→ split_case_sections()
  │   ├→ Scan for Arabic keywords
  │   ├→ Extract content between markers
  │   └→ Return sections dict
  ↓
  ├→ save_case_with_sections()
  │   ├→ Create LegalCase
  │   └→ Create CaseSection (x N)
  ↓
  └→ Update status to 'processed'
       ↓
     Return success response
```

### JSON Upload Flow

```
Client
  ↓ (HTTP POST with JSON file)
Router (Validation)
  ↓
LegalCaseService.upload_json_case_structure()
  ↓
  For each case in JSON:
    ├→ Generate unique hash
    ├→ Create KnowledgeDocument
    ├→ Create LegalCase
    ├→ For each section:
    │   ├→ Create CaseSection
    │   └→ Create KnowledgeChunk
    ↓
  Commit transaction
  ↓
  Return success with statistics
```

### Get Case Flow

```
Client
  ↓ (HTTP GET /{case_id})
Router
  ↓
LegalCaseService.get_legal_case()
  ↓
  ├→ LegalCaseRepository.get_case_by_id()
  │   └→ SELECT with sections preloaded
  ↓
  ├→ Format case data
  ├→ If include_sections:
  │   └→ CaseSectionRepository.get_sections_by_case()
  ↓
  Return success response
```

---

## 🎯 Key Design Decisions

### 1. **Clean Architecture**

**Why**: Separation of concerns, testability, maintainability

**Layers**:
- Router: Thin layer for HTTP handling
- Service: Business logic, orchestration
- Repository: Data access, SQL queries
- Model: Database entities

---

### 2. **Unified Response Format**

**Why**: Consistency for frontend integration

**Format**:
```json
{
  "success": bool,
  "message": string,
  "data": object | array | null,
  "errors": array
}
```

---

### 3. **Duplicate Detection**

**Why**: Prevent storing same file multiple times

**Method**: SHA-256 hash of file content

**Check**: Before saving, query `KnowledgeDocument` by `file_hash`

---

### 4. **Arabic Text Processing**

**Why**: PDF extraction often fragments Arabic text

**Solution**:
1. Clean Unicode artifacts
2. Normalize fragmented text
3. Apply Arabic reshaping
4. Apply BiDi algorithm

---

### 5. **Section Segmentation**

**Why**: Structure cases into logical parts

**Method**: Regex patterns for Arabic keywords

**Fallback**: If no markers found, entire text → summary

---

### 6. **JSON Upload Support**

**Why**: Bulk import of pre-processed cases

**Benefit**: Skip file parsing, directly create structured data

**Use Case**: Importing from external systems or manual curation

---

### 7. **KnowledgeDocument as Central Entity**

**Why**: Link all content to a central document record

**Benefits**:
- Track file metadata
- Duplicate detection
- Chunking for embeddings
- Analysis results

---

### 8. **Cascade Delete for Sections**

**Why**: Maintain referential integrity

**Implementation**: SQLAlchemy `cascade="all, delete-orphan"`

**Note**: KnowledgeDocument is NOT deleted (only link removed)

---

## 📝 Usage Examples

### Example 1: Upload PDF Case

```bash
curl -X POST "http://localhost:8000/api/v1/legal-cases/upload" \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -F "file=@case_123.pdf" \
  -F "title=قضية عمالية - إنهاء خدمات" \
  -F "case_number=123/2024" \
  -F "jurisdiction=الرياض" \
  -F "court_name=المحكمة العمالية بالرياض" \
  -F "decision_date=2024-01-15" \
  -F "case_type=عمل" \
  -F "court_level=ابتدائي"
```

---

### Example 2: Upload JSON Structure

```bash
curl -X POST "http://localhost:8000/api/v1/legal-cases/upload-json" \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -F "json_file=@case_structure.json"
```

**case_structure.json**:
```json
{
  "legal_cases": [
    {
      "case_number": "123/2024",
      "title": "قضية عمالية - إنهاء خدمات",
      "description": "نزاع حول إنهاء خدمات عامل",
      "jurisdiction": "الرياض",
      "court_name": "المحكمة العمالية بالرياض",
      "decision_date": "2024-01-15",
      "case_type": "عمل",
      "court_level": "ابتدائي",
      "sections": [
        {
          "section_type": "summary",
          "content": "ملخص القضية: نزاع بين عامل وصاحب عمل حول إنهاء الخدمات بدون مبرر قانوني..."
        },
        {
          "section_type": "facts",
          "content": "وقائع القضية: تقدم العامل بشكوى ضد صاحب العمل بتاريخ 2024-01-10..."
        },
        {
          "section_type": "ruling",
          "content": "الحكم: حكمت المحكمة بإلزام صاحب العمل بدفع تعويض قدره 50,000 ريال..."
        }
      ]
    }
  ]
}
```

---

### Example 3: List Cases with Filters

```bash
curl -X GET "http://localhost:8000/api/v1/legal-cases/?jurisdiction=الرياض&case_type=عمل&limit=10" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

---

### Example 4: Get Case with Sections

```bash
curl -X GET "http://localhost:8000/api/v1/legal-cases/123?include_sections=true" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

---

### Example 5: Update Case

```bash
curl -X PUT "http://localhost:8000/api/v1/legal-cases/123" \
  -H "Authorization: Bearer {JWT_TOKEN}" \
  -F "title=قضية عمالية محدثة" \
  -F "description=نزاع حول إنهاء خدمات عامل - تم التحديث"
```

---

### Example 6: Delete Case

```bash
curl -X DELETE "http://localhost:8000/api/v1/legal-cases/123" \
  -H "Authorization: Bearer {JWT_TOKEN}"
```

---

## 🔍 Testing Checklist

### Unit Tests

- [ ] LegalCaseService.list_legal_cases()
- [ ] LegalCaseService.get_legal_case()
- [ ] LegalCaseService.upload_json_case_structure()
- [ ] LegalCaseIngestionService.extract_text() (PDF/DOCX/TXT)
- [ ] LegalCaseIngestionService.split_case_sections()
- [ ] LegalCaseIngestionService._fix_arabic_text()

### Integration Tests

- [ ] POST /upload (valid PDF)
- [ ] POST /upload (invalid file type)
- [ ] POST /upload (duplicate file)
- [ ] POST /upload-json (valid JSON)
- [ ] POST /upload-json (invalid JSON)
- [ ] GET / (list with filters)
- [ ] GET /{id} (valid case)
- [ ] GET /{id} (non-existent case)
- [ ] PUT /{id} (update case)
- [ ] DELETE /{id} (delete case)
- [ ] GET /{id}/sections (get sections)

### End-to-End Tests

- [ ] Upload PDF → Extract → Segment → Store → Verify in DB
- [ ] Upload JSON → Parse → Store → Verify in DB
- [ ] Upload → List → Get → Update → Delete (full lifecycle)

---

## 📚 Dependencies

### Python Packages

```txt
fastapi>=0.109.0
sqlalchemy[asyncio]>=2.0.25
pydantic>=2.5.3
python-multipart  # For file uploads
PyMuPDF  # PDF extraction
python-docx  # DOCX extraction
arabic-reshaper  # Arabic text processing
python-bidi  # BiDi algorithm
```

### External Services

- **Database**: SQLite (development) / PostgreSQL (production)
- **File Storage**: Local filesystem (`uploads/legal_cases/`)
- **Authentication**: JWT tokens

---

## 🚀 Performance Considerations

### 1. **File Upload Optimization**

- Stream large files instead of loading entirely into memory
- Use async file I/O
- Validate file size before processing

---

### 2. **PDF Extraction Optimization**

- Process pages in parallel (if needed)
- Cache extracted text
- Implement timeout for large files

---

### 3. **Database Optimization**

- Use indexes on frequently queried fields
- Preload relationships with `selectinload()`
- Implement pagination for large result sets
- Use connection pooling

---

### 4. **Arabic Text Processing**

- Apply fixing only when needed (check `_needs_fixing()`)
- Process text in chunks if very large
- Cache reshaping results if same text appears multiple times

---

## 📊 Monitoring & Logging

### Logging Levels

```python
logger.info("Step 1: Saving uploaded file...")
logger.warning("No section markers found, using entire text as summary")
logger.error("Failed to extract text from PDF")
logger.exception("Unexpected error during legal case upload")
```

### Key Metrics to Monitor

- **Upload Success Rate**: % of successful uploads
- **Extraction Time**: Time to extract text from PDF
- **Section Detection Rate**: % of cases with detected sections
- **API Response Time**: Time to process requests
- **Error Rate**: % of failed requests

---

## 🔮 Future Enhancements

### 1. **OCR Support**

For image-based PDFs (scanned documents):
- Integrate Tesseract OCR
- Pre-process images for better accuracy
- Support multi-language OCR

---

### 2. **Advanced Section Detection**

- Machine learning-based section classification
- Custom section types per court/jurisdiction
- Automatic legal entity extraction

---

### 3. **Batch Upload**

- Support uploading multiple files at once
- Background processing with job queue (Celery)
- Progress tracking

---

### 4. **Embeddings & Search**

- Generate embeddings for sections
- Store in FAISS index
- Semantic search across cases
- Similar case recommendations

---

### 5. **Legal Analysis**

- Extract cited laws/articles
- Link cases to legal sources
- Generate case summaries with AI
- Identify precedents

---

### 6. **Export & Reporting**

- Export cases to PDF/DOCX
- Generate case reports
- Statistics dashboard
- Bulk export

---

## ✅ Summary

This document provides a **complete picture** of the Legal Cases system:

1. **Architecture**: Clean separation of router → service → repository → model
2. **Workflows**: Detailed flow for file upload, JSON upload, CRUD operations
3. **Data Models**: Full schema with relationships and constraints
4. **Error Handling**: Unified response format with comprehensive error handling
5. **Arabic Processing**: Advanced text fixing for fragmented PDF extraction
6. **Section Segmentation**: Regex-based keyword detection
7. **Authentication**: JWT-based auth with current_user injection

**Key Strengths**:
✅ Clean architecture with clear separation of concerns  
✅ Comprehensive error handling and validation  
✅ Advanced Arabic text processing  
✅ Unified API response format  
✅ Duplicate detection with file hashing  
✅ Flexible upload options (file or JSON)  
✅ Full CRUD operations with filtering  

---

**Last Updated**: January 2024  
**Version**: 1.0  
**Maintainer**: AI Legal Assistant Team
