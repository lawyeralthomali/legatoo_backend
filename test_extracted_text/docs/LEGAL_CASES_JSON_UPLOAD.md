# Legal Cases JSON Upload API

## Overview

This document describes the JSON upload endpoint for legal cases, which allows you to bulk import legal case data directly into the system without uploading PDF files.

## Endpoint

```
POST /api/v1/legal-cases/upload-json
```

## Authentication

Requires a valid JWT token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Request

### Content-Type
```
multipart/form-data
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| json_file | File | Yes | JSON file containing legal case structure |

## JSON Structure

### Root Object

```json
{
  "legal_cases": [
    // Array of legal case objects
  ],
  "processing_report": {
    // Optional metadata about the upload
  }
}
```

### Legal Case Object

Each case in the `legal_cases` array should follow this structure:

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| case_number | string | No | Case reference number | e.g., "123/1445" |
| title | string | Yes | Case title | Any string |
| description | string | No | Brief description | Any string |
| jurisdiction | string | No | Legal jurisdiction | e.g., "الرياض", "جدة" |
| court_name | string | No | Name of the court | e.g., "المحكمة العمالية بالرياض" |
| decision_date | string | No | Date of decision | YYYY-MM-DD format |
| case_type | string | No | Type of case | "مدني", "جنائي", "تجاري", "عمل", "إداري" |
| court_level | string | No | Court level | "ابتدائي", "استئناف", "تمييز", "عالي" |
| sections | array | No | Array of case sections | See section object below |

### Case Section Object

Each section in the `sections` array should follow this structure:

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| section_type | string | Yes | Type of section | "summary", "facts", "arguments", "ruling", "legal_basis" |
| content | string | Yes | Section content | Any text content |

### Section Types Explained

- **summary** (ملخص): Brief overview of the case
- **facts** (الوقائع): Facts and circumstances of the case
- **arguments** (الحجج): Arguments from both parties
- **ruling** (الحكم): Court's decision and judgment
- **legal_basis** (الأساس القانوني): Legal basis and referenced laws/articles

### Processing Report (Optional)

```json
{
  "total_cases": 2,
  "warnings": [],
  "errors": [],
  "suggestions": ["تحقق من اكتمال البيانات"]
}
```

## Complete Example

```json
{
  "legal_cases": [
    {
      "case_number": "123/1445",
      "title": "قضية عمالية - إنهاء خدمات بدون مبرر",
      "description": "نزاع بين عامل وصاحب عمل حول إنهاء خدمات العامل",
      "jurisdiction": "الرياض",
      "court_name": "المحكمة العمالية بالرياض",
      "decision_date": "2024-03-15",
      "case_type": "عمل",
      "court_level": "ابتدائي",
      "sections": [
        {
          "section_type": "summary",
          "content": "ملخص القضية: تقدم العامل بدعوى ضد صاحب العمل للمطالبة بتعويض..."
        },
        {
          "section_type": "facts",
          "content": "وقائع القضية: عمل المدعي لدى الشركة لمدة 5 سنوات..."
        },
        {
          "section_type": "arguments",
          "content": "حجج الأطراف: ادعى العامل أن إنهاء خدماته كان تعسفياً..."
        },
        {
          "section_type": "ruling",
          "content": "الحكم: حكمت المحكمة بإلزام الشركة بدفع تعويض قدره 80,000 ريال..."
        },
        {
          "section_type": "legal_basis",
          "content": "الأساس القانوني: استندت المحكمة إلى المادة 74 من نظام العمل..."
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

## Response

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "✅ Successfully processed JSON case structure: Successfully processed 2 legal case(s) with 10 section(s)",
  "data": {
    "cases": [
      {
        "id": 1,
        "case_number": "123/1445",
        "title": "قضية عمالية - إنهاء خدمات بدون مبرر"
      },
      {
        "id": 2,
        "case_number": "456/1445",
        "title": "قضية تجارية - نزاع شراكة"
      }
    ],
    "statistics": {
      "total_cases": 2,
      "total_sections": 10,
      "processing_report": {
        "total_cases": 2,
        "warnings": [],
        "errors": [],
        "suggestions": ["تحقق من اكتمال البيانات"]
      }
    }
  },
  "errors": []
}
```

### Error Responses

#### Invalid File Type (400)
```json
{
  "success": false,
  "message": "Invalid file type. Only JSON files are supported",
  "data": null,
  "errors": []
}
```

#### Invalid JSON Format (400)
```json
{
  "success": false,
  "message": "Invalid JSON format: Expecting value: line 1 column 1 (char 0)",
  "data": null,
  "errors": []
}
```

#### Missing legal_cases Array (400)
```json
{
  "success": false,
  "message": "Invalid JSON structure. Missing 'legal_cases' array",
  "data": null,
  "errors": [
    {
      "field": "legal_cases",
      "message": "Missing or empty legal_cases array"
    }
  ]
}
```

#### Processing Error (500)
```json
{
  "success": false,
  "message": "Failed to upload JSON case structure: <error details>",
  "data": null,
  "errors": [
    {
      "field": null,
      "message": "<error details>"
    }
  ]
}
```

## Backend Processing Flow

1. **File Validation**
   - Verify file is JSON format
   - Parse JSON content

2. **Structure Validation**
   - Check for `legal_cases` array
   - Validate required fields

3. **For Each Case:**
   - Generate unique hash based on content
   - Create `KnowledgeDocument` record
   - Create `LegalCase` record
   - Create `CaseSection` records for each section
   - Create `KnowledgeChunk` records for searchability

4. **Commit Transaction**
   - Save all records to database
   - Return statistics and created case IDs

## Database Impact

For each uploaded case, the following records are created:

- **1 KnowledgeDocument**: Stores metadata about the JSON upload
- **1 LegalCase**: Main case record with metadata
- **N CaseSections**: One per section in the JSON (typically 5)
- **N KnowledgeChunks**: One per section for search indexing

## Use Cases

### 1. Bulk Import Historical Cases
Upload multiple cases at once from existing databases or archives.

### 2. AI-Extracted Cases
Upload cases that have been extracted and structured by AI systems.

### 3. Manual Case Entry via JSON
Create cases programmatically without going through file upload process.

### 4. Data Migration
Migrate case data from other legal systems or databases.

## Testing with cURL

```bash
curl -X POST "http://localhost:8000/api/v1/legal-cases/upload-json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "json_file=@sample_case_upload.json"
```

## Testing with Python

```python
import requests

url = "http://localhost:8000/api/v1/legal-cases/upload-json"
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

with open("sample_case_upload.json", "rb") as f:
    files = {"json_file": f}
    response = requests.post(url, headers=headers, files=files)
    print(response.json())
```

## Best Practices

1. **Validate JSON First**: Use a JSON validator before uploading
2. **Use Descriptive Titles**: Make case titles clear and searchable
3. **Include All Section Types**: Provide comprehensive case information
4. **Date Format**: Always use YYYY-MM-DD format for dates
5. **Arabic Text**: Ensure proper UTF-8 encoding for Arabic content
6. **Batch Processing**: Group related cases in single JSON file
7. **Error Handling**: Check response for any warnings or errors

## Comparison with PDF Upload

| Feature | JSON Upload | PDF Upload |
|---------|-------------|------------|
| Processing Speed | ⚡ Instant | 🐌 Slow (requires parsing) |
| Accuracy | ✅ 100% | ❓ Depends on PDF quality |
| Structure Control | ✅ Full control | ⚠️ AI-dependent |
| Bulk Upload | ✅ Multiple cases | ❌ One at a time |
| Source Document | ❌ No file stored | ✅ PDF archived |
| AI Processing | ❌ Pre-structured | ✅ Required |

## Sample Files

A sample JSON file is available at:
```
data_set/sample_case_upload.json
```

This file contains two example cases (one labor case and one commercial case) with all required sections.

## Related Endpoints

- `POST /api/v1/legal-cases/upload` - Upload case from PDF/DOCX file
- `GET /api/v1/legal-cases/` - List all legal cases
- `GET /api/v1/legal-cases/{case_id}` - Get specific case details
- `PUT /api/v1/legal-cases/{case_id}` - Update case metadata
- `DELETE /api/v1/legal-cases/{case_id}` - Delete a case

## Notes

- The uploaded JSON is not stored as a physical file
- A unique hash is generated based on JSON content to prevent duplicates
- All cases are marked as "processed" status immediately
- Knowledge chunks are created automatically for search functionality
- Similar functionality exists for laws at `/api/v1/legal-laws/upload-json`

## Support

For issues or questions about this endpoint, check:
1. Application logs at `logs/app.log`
2. Database records in `legal_cases` and `case_sections` tables
3. API documentation at `/docs` (Swagger UI)
