"""
Document Upload API Documentation and Examples

This module provides comprehensive documentation and examples for the
legal document upload API endpoint.
"""

# Example JSON Document Structure
EXAMPLE_JSON_DOCUMENT = {
    "law_sources": [
        {
            "name": "نظام العمل السعودي",
            "type": "law",
            "jurisdiction": "المملكة العربية السعودية",
            "issuing_authority": "وزارة الموارد البشرية والتنمية الاجتماعية",
            "issue_date": "2023-01-01",
            "last_update": "2023-12-01",
            "description": "النظام الأساسي لتنظيم علاقات العمل في المملكة العربية السعودية",
            "source_url": "https://mlsd.gov.sa/laws/labor-law",
            "articles": [
                {
                    "article": "1",
                    "title": "تعريفات",
                    "text": "في تطبيق أحكام هذا النظام يقصد بالكلمات والعبارات التالية المعاني المبينة أمام كل منها ما لم يقتض السياق خلاف ذلك:\n\nالعامل: كل شخص طبيعي يعمل لدى صاحب عمل لقاء أجر مهما كان نوع الأجر.\nصاحب العمل: كل شخص طبيعي أو اعتباري يستخدم عاملاً أو أكثر لقاء أجر.\nالأجر: كل ما يعطى للعامل مقابل عمله نقداً أو عيناً مهما كان نوعه.",
                    "keywords": ["تعريفات", "عامل", "صاحب عمل", "أجر"],
                    "order_index": 1
                },
                {
                    "article": "2",
                    "title": "نطاق التطبيق",
                    "text": "يطبق هذا النظام على جميع العمال وأصحاب العمل في المملكة العربية السعودية، عدا:\n\n1- عمال الحكومة والقطاع العام.\n2- عمال الخدمة المنزلية.\n3- عمال الزراعة والرعي.\n4- عمال البحرية التجارية.\n5- عمال المناجم والمحاجر.",
                    "keywords": ["نطاق التطبيق", "عمال", "أصحاب عمل", "استثناءات"],
                    "order_index": 2
                },
                {
                    "article": "3",
                    "title": "مبادئ أساسية",
                    "text": "يستند هذا النظام إلى المبادئ الأساسية التالية:\n\n1- المساواة في الحقوق والواجبات بين العمال وأصحاب العمل.\n2- حرية العمل وحظر السخرة.\n3- حماية حقوق العمال وضمان شروط عمل عادلة.\n4- تشجيع الاستثمار وتنمية الاقتصاد الوطني.\n5- احترام القيم الإسلامية والاجتماعية.",
                    "keywords": ["مبادئ أساسية", "مساواة", "حرية العمل", "حماية حقوق"],
                    "order_index": 3
                }
            ]
        },
        {
            "name": "نظام الضمان الاجتماعي",
            "type": "regulation",
            "jurisdiction": "المملكة العربية السعودية",
            "issuing_authority": "المؤسسة العامة للضمان الاجتماعي",
            "issue_date": "2022-06-01",
            "last_update": "2023-11-15",
            "description": "النظام المنظم لضمانات العمال الاجتماعية",
            "source_url": "https://gosi.gov.sa/regulations",
            "articles": [
                {
                    "article": "1",
                    "title": "أهداف النظام",
                    "text": "يهدف نظام الضمان الاجتماعي إلى:\n\n1- توفير الحماية الاجتماعية للعمال.\n2- ضمان حقوق التقاعد والرعاية الصحية.\n3- دعم العمال في حالات الطوارئ.\n4- تشجيع الاستقرار الوظيفي.",
                    "keywords": ["أهداف", "حماية اجتماعية", "تقاعد", "رعاية صحية"],
                    "order_index": 1
                }
            ]
        }
    ]
}

# Example API Request
EXAMPLE_API_REQUEST = """
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: [JSON file content]
title: "نظام العمل السعودي 2023"
category: "law"
uploaded_by: 1
"""

# Example API Response
EXAMPLE_API_RESPONSE = {
    "success": True,
    "message": "Document 'نظام العمل السعودي 2023' uploaded and processed successfully",
    "data": {
        "document_id": 123,
        "title": "نظام العمل السعودي 2023",
        "category": "law",
        "file_path": "uploads/20241201_143022_labor_law.json",
        "file_hash": "a1b2c3d4e5f6...",
        "status": "processed",
        "uploaded_at": "2024-12-01T14:30:22Z",
        "chunks_created": 15,
        "law_sources_processed": 2,
        "articles_processed": 4,
        "law_sources": [
            {
                "id": 45,
                "name": "نظام العمل السعودي",
                "type": "law",
                "jurisdiction": "المملكة العربية السعودية",
                "issuing_authority": "وزارة الموارد البشرية والتنمية الاجتماعية",
                "issue_date": "2023-01-01",
                "articles_count": 3
            },
            {
                "id": 46,
                "name": "نظام الضمان الاجتماعي",
                "type": "regulation",
                "jurisdiction": "المملكة العربية السعودية",
                "issuing_authority": "المؤسسة العامة للضمان الاجتماعي",
                "issue_date": "2022-06-01",
                "articles_count": 1
            }
        ],
        "articles": [
            {
                "id": 201,
                "article_number": "1",
                "title": "تعريفات",
                "order_index": 1
            },
            {
                "id": 202,
                "article_number": "2",
                "title": "نطاق التطبيق",
                "order_index": 2
            },
            {
                "id": 203,
                "article_number": "3",
                "title": "مبادئ أساسية",
                "order_index": 3
            },
            {
                "id": 204,
                "article_number": "1",
                "title": "أهداف النظام",
                "order_index": 1
            }
        ],
        "chunks": [
            {
                "id": 1001,
                "chunk_index": 0,
                "tokens_count": 45,
                "law_source_id": 45,
                "article_id": 201
            },
            {
                "id": 1002,
                "chunk_index": 1,
                "tokens_count": 38,
                "law_source_id": 45,
                "article_id": 201
            }
        ],
        "processing_time_seconds": 2.34,
        "file_size_bytes": 15420,
        "duplicate_detected": False
    },
    "errors": []
}

# Error Response Examples
ERROR_RESPONSE_EXAMPLES = {
    "invalid_file_type": {
        "success": False,
        "message": "Unsupported file type",
        "data": None,
        "errors": [
            {
                "field": "file",
                "message": "File type '.xml' not supported. Allowed types: .json, .pdf, .docx, .doc, .txt"
            }
        ]
    },
    "invalid_category": {
        "success": False,
        "message": "Invalid category",
        "data": None,
        "errors": [
            {
                "field": "category",
                "message": "Category must be one of: law, article, manual, policy, contract"
            }
        ]
    },
    "empty_file": {
        "success": False,
        "message": "Empty file",
        "data": None,
        "errors": [
            {
                "field": "file",
                "message": "File is empty"
            }
        ]
    },
    "file_too_large": {
        "success": False,
        "message": "File too large",
        "data": None,
        "errors": [
            {
                "field": "file",
                "message": "File size (52428800 bytes) exceeds maximum allowed size (52428800 bytes)"
            }
        ]
    },
    "invalid_json": {
        "success": False,
        "message": "Document validation failed",
        "data": None,
        "errors": [
            {
                "field": "file",
                "message": "Invalid JSON format: Expecting ',' delimiter: line 5 column 3 (char 45)"
            }
        ]
    }
}

# Usage Instructions
USAGE_INSTRUCTIONS = """
# Legal Document Upload API Usage Guide

## Overview
The Document Upload API allows you to upload and process legal documents in various formats,
with comprehensive parsing, metadata extraction, and knowledge chunking.

## Supported Formats
- **JSON**: Fully supported with hierarchical parsing
- **PDF**: Planned for Q2 2024
- **DOCX**: Planned for Q2 2024  
- **TXT**: Planned for Q1 2024

## JSON Document Structure
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

## API Endpoints

### 1. Upload Document
**POST** `/api/v1/documents/upload`

**Parameters:**
- `file`: Document file (multipart/form-data)
- `title`: Document title (string, required)
- `category`: Document category (string, required)
- `uploaded_by`: User ID (integer, optional)

**Categories:** law, article, manual, policy, contract

### 2. Get Upload Status
**GET** `/api/v1/documents/upload/status/{document_id}`

Returns processing status and statistics for a document.

### 3. Get Supported Formats
**GET** `/api/v1/documents/supported-formats`

Returns information about supported file formats and capabilities.

## Features

### Duplicate Detection
- Uses SHA-256 hash to detect duplicate files
- Prevents processing of identical documents
- Returns duplicate status in response

### Hierarchical Processing
- **Law Sources**: Top-level legal documents
- **Articles**: Individual articles within sources
- **Chunks**: Text segments for search and retrieval

### Bulk Operations
- Optimized database operations
- Batch processing for large documents
- Transaction safety with rollback on errors

### Error Handling
- Comprehensive validation
- Detailed error messages
- Field-specific error reporting

## Example Usage with cURL

```bash
# Upload a JSON legal document
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@labor_law.json" \
  -F "title=نظام العمل السعودي 2023" \
  -F "category=law" \
  -F "uploaded_by=1"

# Check upload status
curl -X GET "http://localhost:8000/api/v1/documents/upload/status/123"

# Get supported formats
curl -X GET "http://localhost:8000/api/v1/documents/supported-formats"
```

## Example Usage with Python

```python
import requests

# Upload document
files = {'file': open('labor_law.json', 'rb')}
data = {
    'title': 'نظام العمل السعودي 2023',
    'category': 'law',
    'uploaded_by': 1
}

response = requests.post(
    'http://localhost:8000/api/v1/documents/upload',
    files=files,
    data=data
)

result = response.json()
print(f"Document ID: {result['data']['document_id']}")
print(f"Chunks created: {result['data']['chunks_created']}")
```

## Response Format
All responses follow the unified API response format:

```json
{
    "success": true|false,
    "message": "Human-readable message",
    "data": {...} | null,
    "errors": [
        {
            "field": "field_name" | null,
            "message": "Error description"
        }
    ]
}
```

## Best Practices

1. **File Validation**: Always validate your JSON structure before upload
2. **Error Handling**: Check the `success` field and handle errors appropriately
3. **Status Monitoring**: Use the status endpoint to monitor processing
4. **Duplicate Prevention**: Check `duplicate_detected` in response
5. **Batch Processing**: For multiple documents, process them sequentially

## Limitations

- Maximum file size: 50MB
- JSON parsing only (other formats planned)
- No OCR support for scanned documents
- Limited text chunking strategies

## Future Enhancements

- Advanced NLP-based chunking
- Multi-language support
- OCR integration
- Document versioning
- Batch upload processing
"""

if __name__ == "__main__":
    print("Document Upload API Documentation")
    print("=" * 50)
    print(USAGE_INSTRUCTIONS)
