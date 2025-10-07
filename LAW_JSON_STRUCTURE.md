# Law JSON Structure Documentation

This document explains the correct JSON structure for uploading law data to the database.

## Overview

The JSON structure is designed specifically for **LAW** data, not legal cases. It follows the hierarchical structure: LawSource → LawBranch → LawChapter → LawArticle.

## Complete JSON Structure

```json
{
  "law_sources": [
    {
      "name": "نظام العمل السعودي",
      "type": "law",
      "jurisdiction": "المملكة العربية السعودية",
      "issuing_authority": "وزارة الموارد البشرية والتنمية الاجتماعية",
      "issue_date": "1426-08-23",
      "last_update": "1442-01-07",
      "description": "نظام العمل السعودي الصادر بالمرسوم الملكي رقم (م/51)",
      "source_url": "https://example.com/law-url",
      "branches": [
        {
          "branch_number": "الأول",
          "branch_name": "التعريفات / الأحكام العامة",
          "description": "يتناول هذا الباب التعريفات الأساسية المستخدمة في نظام العمل",
          "order_index": 1,
          "chapters": [
            {
              "chapter_number": "الأول",
              "chapter_name": "التعريفات",
              "description": "يتضمن تعريفات للمصطلحات الرئيسية المستخدمة في نظام العمل",
              "order_index": 1,
              "articles": [
                {
                  "article_number": "الأولى",
                  "title": "اسم النظام",
                  "content": "يسمى هذا النظام نظام العمل.",
                  "keywords": ["نظام العمل", "اسم النظام"],
                  "order_index": 1
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "processing_report": {
    "structure_confidence": 0.98,
    "total_branches": 3,
    "total_chapters": 6,
    "total_articles": 30,
    "warnings": [],
    "errors": [],
    "suggestions": ["تحقق من ترقيم المواد", "تأكد من اكتمال النصوص"]
  }
}
```

## Field Descriptions

### LawSource (المصدر القانوني)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `name` | string | ✅ | Name of the law | "نظام العمل السعودي" |
| `type` | string | ✅ | Type of law source | "law", "regulation", "code", "directive", "decree" |
| `jurisdiction` | string | ❌ | Jurisdiction or country | "المملكة العربية السعودية" |
| `issuing_authority` | string | ❌ | Authority that issued the law | "وزارة الموارد البشرية والتنمية الاجتماعية" |
| `issue_date` | string | ❌ | Issue date in YYYY-MM-DD format | "1426-08-23" |
| `last_update` | string | ❌ | Last update date in YYYY-MM-DD format | "1442-01-07" |
| `description` | string | ❌ | Description of the law | "نظام العمل السعودي الصادر بالمرسوم الملكي..." |
| `source_url` | string | ❌ | URL to the law source | "https://example.com/law-url" |
| `branches` | array | ✅ | Array of law branches | See LawBranch structure |

### LawBranch (الباب القانوني)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `branch_number` | string | ❌ | Branch number | "الأول", "1", "الباب الأول" |
| `branch_name` | string | ✅ | Branch name | "التعريفات / الأحكام العامة" |
| `description` | string | ❌ | Branch description | "يتناول هذا الباب التعريفات الأساسية..." |
| `order_index` | number | ❌ | Order for sorting (default: 0) | 1 |
| `chapters` | array | ✅ | Array of chapters in this branch | See LawChapter structure |

### LawChapter (الفصل القانوني)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `chapter_number` | string | ❌ | Chapter number | "الأول", "1", "الفصل الأول" |
| `chapter_name` | string | ✅ | Chapter name | "التعريفات" |
| `description` | string | ❌ | Chapter description | "يتضمن تعريفات للمصطلحات الرئيسية..." |
| `order_index` | number | ❌ | Order for sorting (default: 0) | 1 |
| `articles` | array | ✅ | Array of articles in this chapter | See LawArticle structure |

### LawArticle (المادة القانونية)

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `article_number` | string | ❌ | Article number | "الأولى", "1", "المادة الأولى" |
| `title` | string | ❌ | Article title | "اسم النظام" |
| `content` | string | ✅ | Full article content | "يسمى هذا النظام نظام العمل." |
| `keywords` | array | ❌ | Array of keywords | ["نظام العمل", "اسم النظام"] |
| `order_index` | number | ❌ | Order for sorting (default: 0) | 1 |

### ProcessingReport

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `structure_confidence` | number | ❌ | Confidence score (0-1) | 0.98 |
| `total_branches` | number | ❌ | Total number of branches | 3 |
| `total_chapters` | number | ❌ | Total number of chapters | 6 |
| `total_articles` | number | ❌ | Total number of articles | 30 |
| `warnings` | array | ❌ | Array of warnings | [] |
| `errors` | array | ❌ | Array of errors | [] |
| `suggestions` | array | ❌ | Array of suggestions | ["تحقق من ترقيم المواد"] |

## Important Notes

### 1. Law Type Validation
The `type` field must be one of these exact values:
- `"law"` - قانون
- `"regulation"` - لائحة
- `"code"` - مدونة
- `"directive"` - توجيه
- `"decree"` - مرسوم

### 2. Date Format
- `issue_date` and `last_update` must be in `YYYY-MM-DD` format
- Example: `"1426-08-23"` (Hijri calendar) or `"2005-08-23"` (Gregorian calendar)

### 3. Keywords
- `keywords` should be an array of strings
- Each keyword should be a single word or short phrase
- Example: `["نظام العمل", "اسم النظام", "تعريفات"]`

### 4. Order Index
- `order_index` is used for sorting within each level
- Lower numbers appear first
- Default value is 0 if not specified

### 5. Required Structure
- At least one `law_source` is required
- Each law source must have at least one `branch`
- Each branch must have at least one `chapter`
- Each chapter must have at least one `article`

## Database Mapping

The JSON structure maps to these database tables:

```
LawSource (law_sources)
├── LawBranch (law_branches)
│   └── LawChapter (law_chapters)
│       └── LawArticle (law_articles)
└── KnowledgeDocument (knowledge_documents)
    └── KnowledgeChunk (knowledge_chunks)
```

## Example Files

- `data_set/sample_law_structure.json` - Complete example with Saudi Labor Law
- `data_set/extracted_legal_structure.json` - Your extracted data (may need format adjustment)

## Validation

The system will validate:
1. JSON syntax
2. Required fields presence
3. Law type validity
4. Hierarchical structure completeness
5. Data types and formats

## Upload Methods

1. **API Endpoint**: `POST /api/v1/laws/upload-json`
2. **Batch Script**: `python batch_upload_json.py`
3. **Test Script**: `python test_json_upload.py`
