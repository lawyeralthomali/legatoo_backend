# 🗺️ Legal Hierarchy CRUD API - Quick Reference Map

## 📍 Base URL
```
/api/legal-hierarchy
```

---

## 🌳 Hierarchy Structure

```
Law Source (قانون)
  ↓
  └── Branch (الباب)
       ↓
       └── Chapter (الفصل)
            ↓
            └── Article (المادة)
```

---

## 📌 All Endpoints (17 Total)

### 🟦 Branches (الأبواب) - 5 endpoints

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 1 | `POST` | `/branches` | Create branch |
| 2 | `GET` | `/branches/{id}` | Get branch + chapters |
| 3 | `GET` | `/law-sources/{id}/branches` | List branches |
| 4 | `PUT` | `/branches/{id}` | Update branch |
| 5 | `DELETE` | `/branches/{id}` | Delete branch ⚠️ |

---

### 🟩 Chapters (الفصول) - 5 endpoints

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 6 | `POST` | `/chapters` | Create chapter |
| 7 | `GET` | `/chapters/{id}` | Get chapter + articles |
| 8 | `GET` | `/branches/{id}/chapters` | List chapters |
| 9 | `PUT` | `/chapters/{id}` | Update chapter |
| 10 | `DELETE` | `/chapters/{id}` | Delete chapter ⚠️ |

---

### 🟨 Articles (المواد) - 7 endpoints

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 11 | `POST` | `/articles` | Create article |
| 12 | `GET` | `/articles/{id}` | Get article (full) |
| 13 | `GET` | `/articles` | Search + filter |
| 14 | `GET` | `/law-sources/{id}/articles` | By law source |
| 15 | `GET` | `/branches/{id}/articles` | By branch |
| 16 | `GET` | `/chapters/{id}/articles` | By chapter |
| 17 | `PUT` | `/articles/{id}` | Update article |
| 18 | `DELETE` | `/articles/{id}` | Delete article |

⚠️ = Cascade delete (deletes all children)

---

## 🔑 Authentication

All endpoints require:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

Get token from:
```
POST /api/v1/auth/login
```

---

## 📋 Request/Response Flow

### Create Branch Example

**Request:**
```http
POST /api/legal-hierarchy/branches
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "law_source_id": 1,
  "branch_number": "الباب الأول",
  "branch_name": "التعريفات والأحكام العامة",
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
    "description": null,
    "order_index": 0,
    "chapters_count": 0,
    "created_at": "2025-10-05T12:00:00",
    "updated_at": null
  },
  "errors": []
}
```

---

## 🎯 Common Use Cases

### 1️⃣ Create Complete Hierarchy
```
1. POST /branches          → Get branch_id
2. POST /chapters          → Get chapter_id (use branch_id)
3. POST /articles          → Use law_source_id, branch_id, chapter_id
```

### 2️⃣ View Full Tree
```
1. GET /law-sources/{id}/branches       → List all branches
2. GET /branches/{id}/chapters          → For each branch, get chapters
3. GET /chapters/{id}/articles          → For each chapter, get articles
```

### 3️⃣ Search Articles
```
GET /articles?law_source_id=1&search_query=عامل&limit=20
```

### 4️⃣ Update Order
```
PUT /branches/{id}
{
  "order_index": 5
}
```

### 5️⃣ Delete (Cascade)
```
DELETE /branches/{id}  → Also deletes all chapters + articles
```

---

## 📊 Query Parameters

### Pagination (All List Endpoints)
```
?skip=0&limit=100
```

- **skip**: Number of records to skip (default: 0)
- **limit**: Max records to return (default: 100, max: 500)

### Article Search
```
?law_source_id=1&search_query=text&skip=0&limit=20
```

- **law_source_id**: Filter by law source (optional)
- **branch_id**: Filter by branch (optional)
- **chapter_id**: Filter by chapter (optional)
- **search_query**: Search in content/title/number (optional)

**Note**: At least one filter (law_source_id/branch_id/chapter_id) required

---

## 🎨 Response Format

### Success
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...},
  "errors": []
}
```

### Error
```json
{
  "success": false,
  "message": "Error occurred",
  "data": null,
  "errors": [
    {
      "field": "field_name",
      "message": "Error description"
    }
  ]
}
```

### List
```json
{
  "success": true,
  "message": "Retrieved X items",
  "data": {
    "branches": [...],
    "total": 16,
    "skip": 0,
    "limit": 100
  },
  "errors": []
}
```

---

## 🧪 Quick Test Commands

### Get JWT Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### Create Branch
```bash
TOKEN="your_jwt_token"

curl -X POST "http://localhost:8000/api/legal-hierarchy/branches" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "law_source_id": 1,
    "branch_number": "الباب الأول",
    "branch_name": "التعريفات",
    "order_index": 0
  }'
```

### List Branches
```bash
curl "http://localhost:8000/api/legal-hierarchy/law-sources/1/branches" \
  -H "Authorization: Bearer $TOKEN"
```

### Search Articles
```bash
curl "http://localhost:8000/api/legal-hierarchy/articles?law_source_id=1&search_query=عامل" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔒 Required Fields

### Branch
- ✅ `law_source_id` (integer)
- ✅ `branch_name` (string)
- ⚪ `branch_number` (optional)
- ⚪ `description` (optional)
- ⚪ `order_index` (optional, default: 0)

### Chapter
- ✅ `branch_id` (integer)
- ✅ `chapter_name` (string)
- ⚪ `chapter_number` (optional)
- ⚪ `description` (optional)
- ⚪ `order_index` (optional, default: 0)

### Article
- ✅ `law_source_id` (integer)
- ✅ `content` (string)
- ⚪ `branch_id` (optional)
- ⚪ `chapter_id` (optional)
- ⚪ `article_number` (optional)
- ⚪ `title` (optional)
- ⚪ `keywords` (optional, array)
- ⚪ `embedding` (optional, array)
- ⚪ `order_index` (optional, default: 0)

---

## 📖 HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid data |
| 401 | Unauthorized | Missing/invalid token |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Internal error |

---

## 🎯 Swagger UI

Interactive API testing:
```
http://localhost:8000/docs
```

Look for section: **"Legal Hierarchy (CRUD)"**

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `API_ENDPOINTS_MAP.md` | This file - Quick reference |
| `LEGAL_HIERARCHY_CRUD_API.md` | Full API documentation |
| `CRUD_IMPLEMENTATION_SUMMARY.md` | Implementation overview |

---

## ⚡ Quick Tips

### 1. Always Use Pagination
```
?limit=100  # Good
```

### 2. Handle Errors
```python
if response.json()["success"]:
    # Process data
else:
    # Handle errors
```

### 3. Set order_index
```json
{
  "order_index": 0  // First item
}
```

### 4. Use Search
```
?search_query=keyword  // Server-side search
```

### 5. Test in Swagger
```
/docs → Authorize → Try it out
```

---

## 🚀 Ready to Use!

1. ✅ Start server: `uvicorn app.main:app --reload`
2. ✅ Get JWT token: `POST /api/v1/auth/login`
3. ✅ Visit Swagger UI: `http://localhost:8000/docs`
4. ✅ Test endpoints in "Legal Hierarchy (CRUD)" section

---

**Total Endpoints**: 17  
**Authentication**: Required (JWT)  
**Response Format**: Unified JSON  
**Status**: ✅ Ready for use
