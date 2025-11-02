# 📖 Similar Laws Endpoint - Complete Business Logic Documentation

## 🎯 Endpoint Overview

**URL**: `POST /api/v1/search/similar-laws`

**Base URL**: `http://192.168.100.18:8000/api/v1/search/similar-laws`

**Purpose**: Performs semantic search to find legal articles and laws that are semantically similar to a user's query, using AI-powered embeddings instead of simple keyword matching.

---

## 🏗️ Architecture Overview

```
User Request
    ↓
[API Endpoint] search_router.py
    ↓
[Service Layer] SemanticSearchService
    ↓
[Embedding Service] EmbeddingService
    ↓
[Database] KnowledgeChunk + LawSource + LawArticle
    ↓
Response with enriched results
```

---

## 📝 Request Parameters

| Parameter       | Type    | Required | Default | Description                                    |
|----------------|---------|----------|---------|------------------------------------------------|
| `query`        | string  | ✅ Yes   | -       | Search query text (Arabic/English), min 3 chars|
| `top_k`        | integer | ❌ No    | 10      | Number of results to return (1-100)            |
| `threshold`    | float   | ❌ No    | 0.7     | Minimum similarity score (0.0-1.0)             |
| `jurisdiction` | string  | ❌ No    | None    | Filter by jurisdiction (e.g., "المملكة العربية السعودية") |
| `law_source_id`| integer | ❌ No    | None    | Filter by specific law ID                      |

**Authentication**: Requires JWT token in Authorization header

---

## 🔄 Complete Business Logic Flow

### **Step 1: Request Reception & Validation**
**File**: `app/routes/search_router.py` (Lines 36-99)

```python
@router.post("/similar-laws", response_model=ApiResponse)
async def search_similar_laws(
    query: str = Query(..., description="Search query text", min_length=3),
    top_k: int = Query(10, description="Number of results", ge=1, le=100),
    threshold: float = Query(0.7, description="Similarity threshold", ge=0.0, le=1.0),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    law_source_id: Optional[int] = Query(None, description="Filter by law source ID"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
```

**What Happens:**
1. **Authentication Check**: Validates JWT token via `get_current_user` dependency
2. **Input Validation**: 
   - Query must be at least 3 characters
   - `top_k` must be between 1-100
   - `threshold` must be between 0.0-1.0
3. **Filter Building**: Constructs filter dictionary from optional parameters

```python
# Validate query
if not query or len(query.strip()) < 3:
    return create_error_response(
        message="Query must be at least 3 characters"
    )

# Build filters
filters = {}
if jurisdiction:
    filters['jurisdiction'] = jurisdiction
if law_source_id:
    filters['law_source_id'] = law_source_id
```

---

### **Step 2: Service Initialization**
**File**: `app/routes/search_router.py` (Line 109)

```python
# Initialize search service
search_service = SemanticSearchService(db)
```

**What Happens:**
- Creates instance of `SemanticSearchService`
- Initializes `EmbeddingService` internally with default model
- Sets up caching mechanism (max 100 queries)

---

### **Step 3: Semantic Search Execution**
**File**: `app/services/semantic_search_service.py` (Lines 131-225)

#### **3.1 Cache Check**
```python
# Check cache
cache_key = f"laws_{query}_{top_k}_{threshold}"
if self.cache_enabled and cache_key in self._query_cache:
    logger.debug(f"📦 Using cached results")
    return self._query_cache[cache_key]
```

**Purpose**: Avoid re-computing embeddings for repeated queries

---

#### **3.2 Query Embedding Generation**
**File**: `app/services/semantic_search_service.py` (Line 160)

```python
# Generate query embedding
query_embedding = self.embedding_service._encode_text(query)
```

**What Happens in `_encode_text()`** (`app/services/embedding_service.py`, Lines 121-149):

1. **Model Loading**: Ensures AI model is loaded
   - Model: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
   - Supports Arabic and English
   - Embedding dimension: 768 dimensions

2. **Text Processing**:
   ```python
   # Truncate if necessary (max 512 tokens ≈ 2048 chars)
   text = self._truncate_text(text)
   
   # Generate embedding using SentenceTransformer
   embedding = self.model.encode(text, convert_to_numpy=True)
   embedding_list = embedding.tolist()  # Convert to list of 768 floats
   ```

3. **Caching**: Stores embedding in memory cache for future use

**Result**: 768-dimensional vector representing the semantic meaning of the query

---

#### **3.3 Database Query Construction**
**File**: `app/services/semantic_search_service.py` (Lines 163-183)

```python
# Build query for law chunks
query_builder = select(KnowledgeChunk).where(
    and_(
        KnowledgeChunk.embedding_vector.isnot(None),
        KnowledgeChunk.embedding_vector != '',
        KnowledgeChunk.law_source_id.isnot(None)  # Only law chunks
    )
)

# Apply filters
if filters:
    if 'law_source_id' in filters:
        query_builder = query_builder.where(
            KnowledgeChunk.law_source_id == filters['law_source_id']
        )
    if 'jurisdiction' in filters:
        # Join with LawSource to filter by jurisdiction
        query_builder = query_builder.join(
            LawSource,
            KnowledgeChunk.law_source_id == LawSource.id
        ).where(LawSource.jurisdiction == filters['jurisdiction'])

result = await self.db.execute(query_builder)
chunks = result.scalars().all()
```

**What Happens:**
1. Fetches all `KnowledgeChunk` records that:
   - Have embeddings generated
   - Are associated with a law (not cases)
   - Match the optional filters
2. Returns potentially hundreds of chunks

---

#### **3.4 Similarity Calculation**
**File**: `app/services/semantic_search_service.py` (Lines 194-209)

```python
# Calculate similarities
results = []
for chunk in chunks:
    try:
        similarity = self._calculate_relevance_score(
            query_embedding,
            chunk,
            boost_factors={'verified_boost': True}
        )
        
        if similarity >= threshold:
            # Enrich with metadata
            enriched_result = await self._enrich_law_result(chunk, similarity)
            results.append(enriched_result)
    except Exception as e:
        logger.warning(f"⚠️ Failed to process chunk {chunk.id}: {str(e)}")
        continue
```

**Similarity Calculation Details** (`_calculate_relevance_score`, Lines 89-127):

1. **Parse Chunk Embedding**:
   ```python
   chunk_embedding = json.loads(chunk.embedding_vector)  # Parse stored embedding
   ```

2. **Cosine Similarity Calculation** (`_cosine_similarity`, Lines 56-87):
   ```python
   vec1 = np.array(query_embedding)  # 768 dimensions
   vec2 = np.array(chunk_embedding)  # 768 dimensions
   
   # Cosine similarity formula
   dot_product = np.dot(vec1, vec2)
   norm1 = np.linalg.norm(vec1)
   norm2 = np.linalg.norm(vec2)
   
   similarity = dot_product / (norm1 * norm2)  # Range: -1 to 1 (typically 0 to 1)
   ```

3. **Apply Boost Factors**:
   ```python
   # Verified content boost (10% increase)
   if boost_factors.get('verified_boost') and chunk.verified_by_admin:
       base_score *= 1.1
   
   # Recency boost (5% increase for content < 30 days old)
   if boost_factors.get('recency_boost'):
       days_old = (datetime.utcnow() - chunk.created_at).days
       if days_old < 30:
           base_score *= 1.05
   
   return min(base_score, 1.0)  # Cap at 1.0
   ```

4. **Threshold Filtering**: Only includes results with `similarity >= threshold`

---

#### **3.5 Result Enrichment**
**File**: `app/services/semantic_search_service.py` (Lines 227-306)

For each matching chunk, the system enriches the result with comprehensive metadata:

```python
async def _enrich_law_result(chunk: KnowledgeChunk, similarity: float):
```

**Enrichment Process:**

1. **Base Chunk Data**:
   ```python
   result = {
       'chunk_id': chunk.id,
       'content': chunk.content,
       'similarity': round(similarity, 4),
       'source_type': 'law',
       'chunk_index': chunk.chunk_index,
       'tokens_count': chunk.tokens_count,
       'verified': chunk.verified_by_admin
   }
   ```

2. **Law Source Metadata** (if `chunk.law_source_id` exists):
   - Queries `LawSource` table
   - Adds:
     ```python
     'law_metadata': {
         'law_id': law_source.id,
         'law_name': law_source.name,           # e.g., "نظام العمل"
         'law_type': law_source.type,           # e.g., "law", "regulation"
         'jurisdiction': law_source.jurisdiction,
         'issue_date': law_source.issue_date.isoformat()
     }
     ```

3. **Article Metadata** (if `chunk.article_id` exists):
   - Queries `LawArticle` table
   - Adds:
     ```python
     'article_metadata': {
         'article_id': article.id,
         'article_number': article.article_number,  # e.g., "74"
         'title': article.title,
         'keywords': article.keywords
     }
     ```

4. **Branch Metadata** (if `chunk.branch_id` exists):
   - Queries `LawBranch` table
   - Adds branch hierarchy information

5. **Chapter Metadata** (if `chunk.chapter_id` exists):
   - Queries `LawChapter` table
   - Adds chapter organization information

---

#### **3.6 Sorting & Limiting**
**File**: `app/services/semantic_search_service.py` (Lines 211-217)

```python
# Sort by similarity and take top_k
results.sort(key=lambda x: x['similarity'], reverse=True)
results = results[:top_k]

# Cache results
if self.cache_enabled and len(self._query_cache) < self._cache_max_size:
    self._query_cache[cache_key] = results
```

**What Happens:**
1. Sorts all matching results by similarity score (highest first)
2. Takes only the top K results
3. Caches the final results for future identical queries

---

### **Step 4: Response Formatting**
**File**: `app/routes/search_router.py` (Lines 119-134)

```python
# Format response
response_data = {
    "query": query.strip(),
    "results": results,
    "total_results": len(results),
    "threshold": threshold
}

message = f"Found {len(results)} similar laws"
if filters:
    message += " (with filters)"

return create_success_response(
    message=message,
    data=response_data
)
```

---

## 📤 Response Structure

### Success Response

```json
{
  "success": true,
  "message": "Found 8 similar laws",
  "data": {
    "query": "فسخ عقد العمل",
    "results": [
      {
        "chunk_id": 123,
        "content": "المادة 74: يجوز لصاحب العمل فسخ العقد دون مكافأة أو إنذار في حالة...",
        "similarity": 0.8945,
        "source_type": "law",
        "chunk_index": 15,
        "tokens_count": 256,
        "verified": true,
        "law_metadata": {
          "law_id": 5,
          "law_name": "نظام العمل السعودي",
          "law_type": "law",
          "jurisdiction": "المملكة العربية السعودية",
          "issue_date": "2005-04-23"
        },
        "article_metadata": {
          "article_id": 74,
          "article_number": "74",
          "title": "فسخ عقد العمل من قبل صاحب العمل",
          "keywords": ["فسخ", "عقد العمل", "إنهاء الخدمة"]
        },
        "branch_metadata": {
          "branch_id": 3,
          "branch_number": "الباب الثالث",
          "branch_name": "إنهاء عقد العمل"
        },
        "chapter_metadata": {
          "chapter_id": 8,
          "chapter_number": "الفصل الأول",
          "chapter_name": "فسخ العقد"
        }
      },
      {
        "chunk_id": 145,
        "content": "المادة 75: إذا أنهى أحد الطرفين العقد المحدد المدة...",
        "similarity": 0.8523,
        "source_type": "law",
        "chunk_index": 16,
        "tokens_count": 198,
        "verified": true,
        "law_metadata": {
          "law_id": 5,
          "law_name": "نظام العمل السعودي",
          "law_type": "law",
          "jurisdiction": "المملكة العربية السعودية",
          "issue_date": "2005-04-23"
        },
        "article_metadata": {
          "article_id": 75,
          "article_number": "75",
          "title": "التعويض عن إنهاء العقد المحدد المدة",
          "keywords": ["تعويض", "عقد محدد المدة", "إنهاء"]
        }
      }
      // ... more results up to top_k
    ],
    "total_results": 8,
    "threshold": 0.7
  },
  "errors": []
}
```

### Error Response

```json
{
  "success": false,
  "message": "Query must be at least 3 characters",
  "data": null,
  "errors": [
    {
      "field": "query",
      "message": "Query must be at least 3 characters"
    }
  ]
}
```

---

## 🔍 Data Extraction Process

### How Data is Stored

1. **Law Upload**: 
   - Laws are uploaded via `/api/v1/laws/upload` endpoint
   - PDF/text files are parsed and split into chunks
   - Each chunk is stored in `KnowledgeChunk` table

2. **Embedding Generation**:
   - For each chunk, an AI model generates a 768-dimensional embedding
   - Embeddings are stored as JSON arrays in `KnowledgeChunk.embedding_vector`
   - This happens via `/api/v1/embeddings/generate-document-embeddings`

3. **Database Schema**:

```
KnowledgeChunk
├── id (primary key)
├── content (text)
├── embedding_vector (JSON: array of 768 floats)
├── chunk_index (position in document)
├── tokens_count
├── law_source_id (FK → LawSource)
├── article_id (FK → LawArticle)
├── branch_id (FK → LawBranch)
├── chapter_id (FK → LawChapter)
├── case_id (FK → LegalCase)
├── document_id (FK → KnowledgeDocument)
└── verified_by_admin (boolean)

LawSource
├── id
├── name (e.g., "نظام العمل")
├── type (law, regulation, code, etc.)
├── jurisdiction
├── issue_date
└── ...

LawArticle
├── id
├── article_number (e.g., "74")
├── title
├── content
├── keywords
└── law_source_id (FK)

LawBranch (Legal hierarchy - major divisions)
├── id
├── branch_number
├── branch_name
└── law_source_id (FK)

LawChapter (Legal hierarchy - subdivisions)
├── id
├── chapter_number
├── chapter_name
└── branch_id (FK)
```

### How Search Works

1. **User Query** → Converted to 768-dimensional embedding vector
2. **Database Query** → Fetches all law chunks with embeddings
3. **Similarity Calculation** → Computes cosine similarity between query embedding and each chunk embedding
4. **Filtering** → Keeps only chunks above threshold
5. **Enrichment** → Joins with related tables to add metadata
6. **Sorting** → Orders by similarity score
7. **Limiting** → Returns top K results

---

## 🎯 Key Features

### 1. **Semantic Understanding**
- Not just keyword matching
- Understands meaning and context
- Works with synonyms and related concepts
- Example: Query "إنهاء الخدمة" will match "فسخ العقد" (both mean termination)

### 2. **Multilingual Support**
- Arabic (primary)
- English
- Mixed queries

### 3. **Performance Optimization**
- **Caching**: Stores up to 100 recent queries
- **Batch Processing**: Processes multiple chunks efficiently
- **Indexing**: Database indexes on foreign keys

### 4. **Filtering Capabilities**
- By jurisdiction (e.g., Saudi Arabia)
- By specific law
- Combined filters

### 5. **Relevance Boosting**
- Verified content: +10% score
- Recent content: +5% score (if < 30 days old)

---

## 🛠️ Technical Stack

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI |
| Database | PostgreSQL (via SQLAlchemy) |
| AI Model | sentence-transformers/paraphrase-multilingual-mpnet-base-v2 |
| Embedding Library | sentence-transformers |
| Vector Operations | NumPy |
| Similarity Metric | Cosine Similarity |
| Authentication | JWT (JSON Web Tokens) |

---

## 📊 Performance Characteristics

| Metric | Value |
|--------|-------|
| Embedding Dimension | 768 |
| Max Input Length | 512 tokens (~2048 chars) |
| Cache Size | 100 queries |
| Batch Size | 32 chunks |
| Similarity Range | 0.0 to 1.0 |
| Default Threshold | 0.7 |
| Default Results | 10 |

---

## 🔐 Security

1. **Authentication Required**: JWT token validation
2. **Input Validation**: All parameters validated
3. **SQL Injection Prevention**: SQLAlchemy ORM (no raw SQL)
4. **Rate Limiting**: (Should be implemented at API gateway level)

---

## 📝 Example Usage

### Python Example

```python
import requests

# Authentication
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

# Simple search
params = {
    "query": "فسخ عقد العمل",
    "top_k": 10,
    "threshold": 0.75
}

response = requests.post(
    "http://192.168.100.18:8000/api/v1/search/similar-laws",
    params=params,
    headers=headers
)

data = response.json()
print(f"Found {data['data']['total_results']} results")

for result in data['data']['results']:
    print(f"Similarity: {result['similarity']}")
    print(f"Content: {result['content'][:100]}...")
    print(f"Law: {result['law_metadata']['law_name']}")
    print("---")
```

### cURL Example

```bash
curl -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=فسخ+عقد+العمل&top_k=10&threshold=0.75" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### With Filters

```bash
curl -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=حقوق+العامل&jurisdiction=المملكة+العربية+السعودية&law_source_id=5&top_k=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🐛 Common Issues & Solutions

### Issue 1: Low Similarity Scores
**Problem**: All results below 0.5 similarity

**Solution**: 
- Lower the threshold parameter
- Refine your query to be more specific
- Check if data has embeddings generated

### Issue 2: No Results Found
**Problem**: `total_results: 0`

**Solution**:
- Verify embeddings are generated for chunks
- Check if filters are too restrictive
- Try lowering the threshold
- Verify data exists in database

### Issue 3: Slow Response Time
**Problem**: Search takes > 5 seconds

**Solution**:
- Enable caching
- Reduce the search space with filters
- Ensure database indexes are present
- Consider using GPU for embeddings

---

## 📚 Related Endpoints

1. **`POST /api/v1/search/similar-cases`** - Search legal cases
2. **`POST /api/v1/search/hybrid`** - Search both laws and cases
3. **`GET /api/v1/search/suggestions`** - Get search suggestions
4. **`GET /api/v1/search/statistics`** - Get search statistics
5. **`POST /api/v1/embeddings/generate-document-embeddings`** - Generate embeddings

---

## 🎓 Understanding Semantic Search

### Traditional Keyword Search vs Semantic Search

**Keyword Search**:
```
Query: "فسخ عقد"
Matches: Only exact words "فسخ" AND "عقد"
Misses: "إنهاء العقد", "إلغاء الاتفاق", "terminate contract"
```

**Semantic Search**:
```
Query: "فسخ عقد"
Matches:
  - "إنهاء عقد العمل" (same meaning)
  - "إلغاء الاتفاق" (related concept)
  - "terminate contract" (English equivalent)
  - "فصل العامل" (related action)
```

### How Embeddings Work

1. **Text → Numbers**: Converts text into 768 numbers (embedding vector)
2. **Similar Meaning = Similar Numbers**: Texts with similar meanings have similar vectors
3. **Distance Measurement**: Cosine similarity measures how "close" two vectors are
4. **Score Interpretation**:
   - 0.9-1.0: Nearly identical meaning
   - 0.8-0.9: Very similar
   - 0.7-0.8: Related
   - 0.6-0.7: Somewhat related
   - < 0.6: Weak relation

---

## 📈 Future Enhancements

1. **FAISS Integration**: Use Facebook AI Similarity Search for faster vector search
2. **Reranking**: Use cross-encoder for more accurate top results
3. **Query Expansion**: Automatically expand queries with synonyms
4. **Personalization**: Learn from user behavior
5. **Multi-modal**: Search by uploading documents
6. **Explanation**: Show why results matched

---

## 🔗 Files Reference

| File | Purpose |
|------|---------|
| `app/routes/search_router.py` | API endpoints |
| `app/services/semantic_search_service.py` | Search business logic |
| `app/services/embedding_service.py` | Embedding generation |
| `app/models/legal_knowledge.py` | Database models |
| `app/schemas/search.py` | Request/response schemas |
| `app/schemas/response.py` | API response formatting |

---

## 📞 Support

For questions or issues:
1. Check logs for detailed error messages
2. Verify authentication token is valid
3. Ensure embeddings are generated for your data
4. Review the example code in this documentation

---

**Last Updated**: October 9, 2025
**API Version**: v1
**Documentation Version**: 1.0

