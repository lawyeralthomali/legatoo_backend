# Legal Hierarchy CRUD API Documentation

## Overview

Complete CRUD (Create, Read, Update, Delete) operations for the legal hierarchy:
- **Law Branches** (الأبواب) - Top-level divisions
- **Law Chapters** (الفصول) - Mid-level sections
- **Law Articles** (المواد) - Individual legal articles

## Architecture

### Clean Architecture Pattern

```
┌─────────────────────────────────────┐
│      API Layer (Router)             │
│  legal_hierarchy_router.py          │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│    Business Logic (Service)         │
│  legal_hierarchy_service.py         │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│   Data Access (Repository)          │
│  legal_hierarchy_repository.py      │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│        Database (Models)            │
│    LawBranch, LawChapter,           │
│        LawArticle                   │
└─────────────────────────────────────┘
```

### Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `app/repositories/legal_hierarchy_repository.py` | ~600 | Database operations |
| `app/services/legal_hierarchy_service.py` | ~750 | Business logic |
| `app/routes/legal_hierarchy_router.py` | ~420 | API endpoints |

---

## API Endpoints

### Base URL
```
/api/legal-hierarchy
```

### Authentication
All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

---

## Branch Endpoints (الأبواب)

### 1. Create Branch
```http
POST /api/legal-hierarchy/branches
```

**Request Body:**
```json
{
  "law_source_id": 1,
  "branch_number": "الباب الأول",
  "branch_name": "التعريفات والأحكام العامة",
  "description": "يتضمن هذا الباب التعريفات الأساسية",
  "order_index": 0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Branch created successfully",
  "data": {
    "id": 1,
    "law_source_id": 1,
    "branch_number": "الباب الأول",
    "branch_name": "التعريفات والأحكام العامة",
    "description": "يتضمن هذا الباب التعريفات الأساسية",
    "order_index": 0,
    "chapters_count": 0,
    "created_at": "2025-10-05T12:00:00",
    "updated_at": null
  },
  "errors": []
}
```

---

### 2. Get Branch by ID
```http
GET /api/legal-hierarchy/branches/{branch_id}
```

**Example:** `GET /api/legal-hierarchy/branches/1`

**Response:**
```json
{
  "success": true,
  "message": "Branch retrieved successfully",
  "data": {
    "id": 1,
    "law_source_id": 1,
    "branch_number": "الباب الأول",
    "branch_name": "التعريفات والأحكام العامة",
    "description": "يتضمن هذا الباب التعريفات الأساسية",
    "order_index": 0,
    "chapters_count": 2,
    "chapters": [
      {
        "id": 1,
        "chapter_number": "الفصل الأول",
        "chapter_name": "التعريفات",
        "description": "تعريفات المصطلحات",
        "order_index": 0
      },
      {
        "id": 2,
        "chapter_number": "الفصل الثاني",
        "chapter_name": "الأحكام العامة",
        "description": "الأحكام العامة للنظام",
        "order_index": 1
      }
    ],
    "created_at": "2025-10-05T12:00:00",
    "updated_at": null
  },
  "errors": []
}
```

---

### 3. List Branches by Law Source
```http
GET /api/legal-hierarchy/law-sources/{law_source_id}/branches
```

**Query Parameters:**
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Max results (default: 100, max: 500)

**Example:** `GET /api/legal-hierarchy/law-sources/1/branches?skip=0&limit=20`

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 16 branches",
  "data": {
    "branches": [
      {
        "id": 1,
        "law_source_id": 1,
        "branch_number": "الباب الأول",
        "branch_name": "التعريفات والأحكام العامة",
        "description": "...",
        "order_index": 0,
        "chapters_count": 2,
        "created_at": "2025-10-05T12:00:00",
        "updated_at": null
      }
      // ... more branches
    ],
    "total": 16,
    "skip": 0,
    "limit": 20
  },
  "errors": []
}
```

---

### 4. Update Branch
```http
PUT /api/legal-hierarchy/branches/{branch_id}
```

**Request Body** (all fields optional):
```json
{
  "branch_number": "الباب الأول",
  "branch_name": "التعريفات والأحكام العامة (محدث)",
  "description": "وصف محدث",
  "order_index": 0
}
```

**Response:** Same as Get Branch

---

### 5. Delete Branch
```http
DELETE /api/legal-hierarchy/branches/{branch_id}
```

⚠️ **Warning:** Cascade deletes all chapters and articles under this branch!

**Response:**
```json
{
  "success": true,
  "message": "Branch deleted successfully",
  "data": {
    "id": 1,
    "deleted": true
  },
  "errors": []
}
```

---

## Chapter Endpoints (الفصول)

### 1. Create Chapter
```http
POST /api/legal-hierarchy/chapters
```

**Request Body:**
```json
{
  "branch_id": 1,
  "chapter_number": "الفصل الأول",
  "chapter_name": "التعريفات",
  "description": "تعريفات المصطلحات القانونية",
  "order_index": 0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Chapter created successfully",
  "data": {
    "id": 1,
    "branch_id": 1,
    "chapter_number": "الفصل الأول",
    "chapter_name": "التعريفات",
    "description": "تعريفات المصطلحات القانونية",
    "order_index": 0,
    "articles_count": 0,
    "created_at": "2025-10-05T12:00:00",
    "updated_at": null
  },
  "errors": []
}
```

---

### 2. Get Chapter by ID
```http
GET /api/legal-hierarchy/chapters/{chapter_id}
```

**Response includes:**
- Chapter details
- List of articles (with truncated content)
- Article count

---

### 3. List Chapters by Branch
```http
GET /api/legal-hierarchy/branches/{branch_id}/chapters
```

**Query Parameters:** `skip`, `limit` (same as branches)

---

### 4. Update Chapter
```http
PUT /api/legal-hierarchy/chapters/{chapter_id}
```

---

### 5. Delete Chapter
```http
DELETE /api/legal-hierarchy/chapters/{chapter_id}
```

⚠️ **Warning:** Cascade deletes all articles under this chapter!

---

## Article Endpoints (المواد)

### 1. Create Article
```http
POST /api/legal-hierarchy/articles
```

**Request Body:**
```json
{
  "law_source_id": 1,
  "branch_id": 1,
  "chapter_id": 1,
  "article_number": "المادة الأولى",
  "title": "تعريف العامل",
  "content": "العامل: كل شخص طبيعي يعمل لمصلحة صاحب عمل وتحت إدارته أو إشرافه مقابل أجر",
  "keywords": ["عامل", "تعريف", "عمل"],
  "order_index": 0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Article created successfully",
  "data": {
    "id": 1,
    "law_source_id": 1,
    "branch_id": 1,
    "chapter_id": 1,
    "article_number": "المادة الأولى",
    "title": "تعريف العامل",
    "content": "العامل: كل شخص طبيعي يعمل لمصلحة صاحب عمل...",
    "keywords": ["عامل", "تعريف", "عمل"],
    "order_index": 0,
    "created_at": "2025-10-05T12:00:00",
    "updated_at": null
  },
  "errors": []
}
```

---

### 2. Get Article by ID
```http
GET /api/legal-hierarchy/articles/{article_id}
```

**Response includes:**
- Full article content
- Related law source, branch, and chapter

---

### 3. List Articles (Flexible Filtering)
```http
GET /api/legal-hierarchy/articles
```

**Query Parameters:**
- `law_source_id` (optional): Filter by law source
- `branch_id` (optional): Filter by branch
- `chapter_id` (optional): Filter by chapter
- `search_query` (optional): Search in content, title, number
- `skip` (optional): Pagination offset
- `limit` (optional): Max results

**Note:** At least one filter (law_source_id, branch_id, or chapter_id) is required

**Example:** `GET /api/legal-hierarchy/articles?law_source_id=1&search_query=عامل&limit=50`

**Response:**
```json
{
  "success": true,
  "message": "Retrieved 5 articles",
  "data": {
    "articles": [
      {
        "id": 1,
        "law_source_id": 1,
        "branch_id": 1,
        "chapter_id": 1,
        "article_number": "المادة الأولى",
        "title": "تعريف العامل",
        "content": "العامل: كل شخص طبيعي يعمل لمصلحة صاحب عمل...",
        "keywords": ["عامل", "تعريف", "عمل"],
        "order_index": 0,
        "created_at": "2025-10-05T12:00:00"
      }
      // ... more articles
    ],
    "total": 5,
    "skip": 0,
    "limit": 50
  },
  "errors": []
}
```

---

### 4. Convenience Endpoints

#### Get Articles by Law Source
```http
GET /api/legal-hierarchy/law-sources/{law_source_id}/articles
```

#### Get Articles by Branch
```http
GET /api/legal-hierarchy/branches/{branch_id}/articles
```

#### Get Articles by Chapter
```http
GET /api/legal-hierarchy/chapters/{chapter_id}/articles
```

---

### 5. Update Article
```http
PUT /api/legal-hierarchy/articles/{article_id}
```

**Request Body** (all fields optional):
```json
{
  "article_number": "المادة الأولى",
  "title": "تعريف العامل (محدث)",
  "content": "محتوى محدث...",
  "keywords": ["عامل", "تعريف", "عمل", "جديد"],
  "branch_id": 1,
  "chapter_id": 1,
  "order_index": 0
}
```

---

### 6. Delete Article
```http
DELETE /api/legal-hierarchy/articles/{article_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Article deleted successfully",
  "data": {
    "id": 1,
    "deleted": true
  },
  "errors": []
}
```

---

## Error Responses

All endpoints follow the unified error format:

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

### Common Errors

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Validation Error | Invalid request data |
| 401 | Unauthorized | Missing or invalid JWT token |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Server Error | Server-side error |

---

## Usage Examples

### Example 1: Create Complete Hierarchy

```python
import requests

base_url = "http://localhost:8000/api/legal-hierarchy"
headers = {"Authorization": f"Bearer {jwt_token}"}

# 1. Create Branch
branch_data = {
    "law_source_id": 1,
    "branch_number": "الباب الأول",
    "branch_name": "التعريفات والأحكام العامة",
    "description": "الباب الأول من النظام",
    "order_index": 0
}
branch_response = requests.post(
    f"{base_url}/branches",
    json=branch_data,
    headers=headers
)
branch_id = branch_response.json()["data"]["id"]

# 2. Create Chapter
chapter_data = {
    "branch_id": branch_id,
    "chapter_number": "الفصل الأول",
    "chapter_name": "التعريفات",
    "description": "تعريفات المصطلحات",
    "order_index": 0
}
chapter_response = requests.post(
    f"{base_url}/chapters",
    json=chapter_data,
    headers=headers
)
chapter_id = chapter_response.json()["data"]["id"]

# 3. Create Article
article_data = {
    "law_source_id": 1,
    "branch_id": branch_id,
    "chapter_id": chapter_id,
    "article_number": "المادة الأولى",
    "title": "تعريف العامل",
    "content": "العامل: كل شخص طبيعي يعمل لمصلحة صاحب عمل...",
    "keywords": ["عامل", "تعريف"],
    "order_index": 0
}
article_response = requests.post(
    f"{base_url}/articles",
    json=article_data,
    headers=headers
)
```

---

### Example 2: Search Articles

```python
# Search for articles containing "عامل"
search_response = requests.get(
    f"{base_url}/articles",
    params={
        "law_source_id": 1,
        "search_query": "عامل",
        "limit": 20
    },
    headers=headers
)

articles = search_response.json()["data"]["articles"]
for article in articles:
    print(f"{article['article_number']}: {article['title']}")
```

---

### Example 3: Get Full Hierarchy

```python
# Get all branches with chapters
law_source_id = 1
branches_response = requests.get(
    f"{base_url}/law-sources/{law_source_id}/branches",
    headers=headers
)

branches = branches_response.json()["data"]["branches"]
for branch in branches:
    print(f"\n{branch['branch_number']}: {branch['branch_name']}")
    
    # Get chapters for this branch
    chapters_response = requests.get(
        f"{base_url}/branches/{branch['id']}/chapters",
        headers=headers
    )
    
    chapters = chapters_response.json()["data"]["chapters"]
    for chapter in chapters:
        print(f"  {chapter['chapter_number']}: {chapter['chapter_name']}")
        
        # Get articles for this chapter
        articles_response = requests.get(
            f"{base_url}/chapters/{chapter['id']}/articles",
            headers=headers
        )
        
        articles = articles_response.json()["data"]["articles"]
        for article in articles:
            print(f"    {article['article_number']}: {article['title']}")
```

---

## Features

### ✅ Complete CRUD Operations
- Create, Read, Update, Delete for all hierarchy levels

### ✅ Cascade Deletes
- Deleting a branch removes all chapters and articles
- Deleting a chapter removes all articles

### ✅ Flexible Filtering
- Filter by law source, branch, or chapter
- Full-text search in articles

### ✅ Pagination
- All list endpoints support skip/limit pagination

### ✅ Statistics
- Automatic counting of child entities (chapters_count, articles_count)

### ✅ Ordering
- `order_index` field for custom display order

### ✅ Unified Response Format
- Consistent JSON structure across all endpoints
- Follows `.cursorrules` API response standards

### ✅ JWT Authentication
- All endpoints require authentication
- User ID tracked for audit trail

### ✅ Comprehensive Error Handling
- Validation errors with field-level details
- Database errors with rollback
- 404 errors for missing resources

---

## Testing

### Swagger UI
Visit `http://localhost:8000/docs` to test all endpoints interactively.

### cURL Examples

```bash
# Create branch
curl -X POST "http://localhost:8000/api/legal-hierarchy/branches" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "law_source_id": 1,
    "branch_number": "الباب الأول",
    "branch_name": "التعريفات والأحكام العامة",
    "order_index": 0
  }'

# List branches
curl "http://localhost:8000/api/legal-hierarchy/law-sources/1/branches" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Search articles
curl "http://localhost:8000/api/legal-hierarchy/articles?law_source_id=1&search_query=عامل" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Best Practices

### 1. Always Use Pagination
```python
# Good
articles = requests.get(f"{base_url}/articles?law_source_id=1&limit=100")

# Bad (might return too many results)
articles = requests.get(f"{base_url}/articles?law_source_id=1")
```

### 2. Set Proper order_index
```python
# Good - explicit ordering
branch_data = {
    "order_index": 0  # First branch
}

# Acceptable - default ordering
branch_data = {
    # order_index defaults to 0
}
```

### 3. Handle Errors Properly
```python
response = requests.post(f"{base_url}/branches", json=data, headers=headers)

if response.json()["success"]:
    branch = response.json()["data"]
    print(f"Created branch: {branch['id']}")
else:
    errors = response.json()["errors"]
    for error in errors:
        print(f"Error in {error['field']}: {error['message']}")
```

### 4. Use Search for Better UX
```python
# Instead of fetching all articles and filtering client-side
articles = get_all_articles(law_source_id)
filtered = [a for a in articles if "عامل" in a["content"]]  # Bad

# Use server-side search
articles = requests.get(
    f"{base_url}/articles",
    params={"law_source_id": 1, "search_query": "عامل"}
)  # Good
```

---

## Performance Considerations

### Efficient Queries
- All queries use proper indexes (law_source_id, branch_id, chapter_id)
- Pagination prevents memory issues
- Selective loading of relationships

### Content Truncation
- List endpoints truncate article content to 300 characters
- Use GET /articles/{id} for full content

### Counting
- Counts are computed efficiently using SQL COUNT()
- Cached in response for quick access

---

## Future Enhancements

### Planned Features
- [ ] Bulk operations (create multiple articles at once)
- [ ] Batch reordering API
- [ ] Export hierarchy to JSON/PDF
- [ ] Version history for articles
- [ ] AI-powered article suggestions
- [ ] Duplicate detection
- [ ] Article comparison

---

## Related Documentation

- **[LEGAL_HIERARCHY_CRUD_API.md](LEGAL_HIERARCHY_CRUD_API.md)** - This file
- **[API_ROUTES_UPDATED.md](API_ROUTES_UPDATED.md)** - All API routes
- **[TOC_DETECTION_COMPREHENSIVE_FIX.md](TOC_DETECTION_COMPREHENSIVE_FIX.md)** - TOC detection fix

---

**Status**: ✅ **READY FOR USE**  
**Date**: October 5, 2025  
**Version**: 1.0.0  
**Endpoints**: 17 total (5 branch + 5 chapter + 7 article)
