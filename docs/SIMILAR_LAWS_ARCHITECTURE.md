# 🏛️ Similar Laws Endpoint - Technical Architecture

## 📐 System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT APPLICATION                               │
│  (Frontend, Mobile App, Third-party Integration)                          │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │
                                   │ HTTPS POST Request
                                   │ Header: Authorization: Bearer <JWT>
                                   │ Params: query, top_k, threshold
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI APPLICATION                                │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    MIDDLEWARE LAYER                                   │ │
│  │  • CORS Middleware                                                    │ │
│  │  • Exception Handlers                                                 │ │
│  │  • Request/Response Logging                                           │ │
│  └───────────────────────────────┬──────────────────────────────────────┘ │
│                                  │                                         │
│  ┌───────────────────────────────▼──────────────────────────────────────┐ │
│  │              API ROUTE: /api/v1/search/similar-laws                  │ │
│  │              File: app/routes/search_router.py                       │ │
│  │                                                                       │ │
│  │  @router.post("/similar-laws")                                       │ │
│  │  async def search_similar_laws(...)                                  │ │
│  │                                                                       │ │
│  │  Responsibilities:                                                    │ │
│  │  ✓ JWT Authentication (get_current_user dependency)                  │ │
│  │  ✓ Input Validation (Query, FastAPI validation)                      │ │
│  │  ✓ Parameter Extraction (query, top_k, threshold, filters)           │ │
│  │  ✓ Error Handling (try/catch → standardized response)                │ │
│  │  ✓ Response Formatting (create_success_response/error_response)      │ │
│  │                                                                       │ │
│  └───────────────────────────────┬──────────────────────────────────────┘ │
│                                  │                                         │
└──────────────────────────────────┼─────────────────────────────────────────┘
                                   │
                                   │ Call service method
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                                      │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │         SemanticSearchService                                         │ │
│  │         File: app/services/semantic_search_service.py                │ │
│  │                                                                       │ │
│  │  async def find_similar_laws(query, top_k, threshold, filters)       │ │
│  │                                                                       │ │
│  │  Flow:                                                                │ │
│  │  ┌────────────────────────────────────────────────────────────┐     │ │
│  │  │ 1. Check Cache                                              │     │ │
│  │  │    cache_key = f"laws_{query}_{top_k}_{threshold}"         │     │ │
│  │  │    if cached → return immediately (20ms)                    │     │ │
│  │  └────────────┬───────────────────────────────────────────────┘     │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────────┐     │ │
│  │  │ 2. Generate Query Embedding                                 │     │ │
│  │  │    query_embedding = embedding_service._encode_text(query)  │     │ │
│  │  │    Returns: List[float] (768 dimensions)                    │     │ │
│  │  └────────────┬───────────────────────────────────────────────┘     │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────────┐     │ │
│  │  │ 3. Build Database Query                                     │     │ │
│  │  │    SELECT * FROM knowledge_chunk                            │     │ │
│  │  │    WHERE embedding_vector IS NOT NULL                       │     │ │
│  │  │      AND law_source_id IS NOT NULL                          │     │ │
│  │  │      [+ optional filters]                                   │     │ │
│  │  └────────────┬───────────────────────────────────────────────┘     │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────────┐     │ │
│  │  │ 4. Calculate Similarities (for each chunk)                  │     │ │
│  │  │    for chunk in chunks:                                     │     │ │
│  │  │        similarity = _calculate_relevance_score(             │     │ │
│  │  │            query_embedding,                                 │     │ │
│  │  │            chunk,                                           │     │ │
│  │  │            boost_factors={'verified_boost': True}           │     │ │
│  │  │        )                                                     │     │ │
│  │  │        if similarity >= threshold:                          │     │ │
│  │  │            results.append(chunk)                            │     │ │
│  │  └────────────┬───────────────────────────────────────────────┘     │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────────┐     │ │
│  │  │ 5. Enrich Results                                           │     │ │
│  │  │    for chunk in results:                                    │     │ │
│  │  │        enriched = await _enrich_law_result(chunk, score)    │     │ │
│  │  │        # Fetches from:                                      │     │ │
│  │  │        # - law_source (law metadata)                        │     │ │
│  │  │        # - law_article (article details)                    │     │ │
│  │  │        # - law_branch (hierarchy)                           │     │ │
│  │  │        # - law_chapter (hierarchy)                          │     │ │
│  │  └────────────┬───────────────────────────────────────────────┘     │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────────┐     │ │
│  │  │ 6. Sort & Limit                                             │     │ │
│  │  │    results.sort(key=similarity, reverse=True)               │     │ │
│  │  │    results = results[:top_k]                                │     │ │
│  │  └────────────┬───────────────────────────────────────────────┘     │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────────┐     │ │
│  │  │ 7. Cache Results                                            │     │ │
│  │  │    _query_cache[cache_key] = results                        │     │ │
│  │  └────────────┬───────────────────────────────────────────────┘     │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │          Return results                                               │ │
│  │                                                                       │ │
│  └───────────────────────────────┬──────────────────────────────────────┘ │
│                                  │                                         │
│                                  │ Uses                                    │
│                                  │                                         │
│  ┌───────────────────────────────▼──────────────────────────────────────┐ │
│  │         EmbeddingService                                              │ │
│  │         File: app/services/embedding_service.py                      │ │
│  │                                                                       │ │
│  │  def _encode_text(text: str) -> List[float]                          │ │
│  │                                                                       │ │
│  │  ┌────────────────────────────────────────────────────────┐         │ │
│  │  │ 1. Check embedding cache                                │         │ │
│  │  │    if text in cache → return cached embedding          │         │ │
│  │  └────────────┬───────────────────────────────────────────┘         │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────┐         │ │
│  │  │ 2. Ensure AI model is loaded                            │         │ │
│  │  │    if model is None:                                    │         │ │
│  │  │        initialize_model()                               │         │ │
│  │  └────────────┬───────────────────────────────────────────┘         │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────┐         │ │
│  │  │ 3. Truncate text if needed                              │         │ │
│  │  │    max_length = 512 tokens (~2048 chars)                │         │ │
│  │  └────────────┬───────────────────────────────────────────┘         │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────┐         │ │
│  │  │ 4. Generate embedding using AI model                    │         │ │
│  │  │    embedding = model.encode(text)                       │         │ │
│  │  │    # Returns numpy array of 768 floats                  │         │ │
│  │  └────────────┬───────────────────────────────────────────┘         │ │
│  │               │                                                       │ │
│  │               ▼                                                       │ │
│  │  ┌────────────────────────────────────────────────────────┐         │ │
│  │  │ 5. Cache & return                                       │         │ │
│  │  │    cache[text] = embedding.tolist()                     │         │ │
│  │  │    return embedding.tolist()                            │         │ │
│  │  └─────────────────────────────────────────────────────────┘         │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Database queries
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE LAYER (PostgreSQL)                        │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  knowledge_chunk                                                      │ │
│  │  ┌──────────────┬──────────────────────────────────────────────────┐ │ │
│  │  │ id           │ Primary Key                                       │ │ │
│  │  │ content      │ Text content of the chunk                         │ │ │
│  │  │ embedding_vector │ JSON: [0.123, -0.456, ..., 0.234] (768)     │ │ │
│  │  │ chunk_index  │ Position in original document                     │ │ │
│  │  │ tokens_count │ Number of tokens                                  │ │ │
│  │  │ law_source_id│ FK → law_source.id                               │ │ │
│  │  │ article_id   │ FK → law_article.id                               │ │ │
│  │  │ branch_id    │ FK → law_branch.id                                │ │ │
│  │  │ chapter_id   │ FK → law_chapter.id                               │ │ │
│  │  │ case_id      │ FK → legal_case.id                                │ │ │
│  │  │ document_id  │ FK → knowledge_document.id                        │ │ │
│  │  │ verified_by_admin │ Boolean                                      │ │ │
│  │  │ created_at   │ Timestamp                                         │ │ │
│  │  └──────────────┴──────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  Indexes:                                                             │ │
│  │  - idx_chunk_law_source (law_source_id)                              │ │
│  │  - idx_chunk_article (article_id)                                    │ │
│  │  - idx_chunk_case (case_id)                                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  law_source                                                           │ │
│  │  ┌──────────────┬──────────────────────────────────────────────────┐ │ │
│  │  │ id           │ Primary Key                                       │ │ │
│  │  │ name         │ "نظام العمل السعودي"                             │ │ │
│  │  │ type         │ law, regulation, code, directive, decree          │ │ │
│  │  │ jurisdiction │ "المملكة العربية السعودية"                        │ │ │
│  │  │ issue_date   │ Date                                              │ │ │
│  │  │ description  │ Text                                              │ │ │
│  │  └──────────────┴──────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  law_article                                                          │ │
│  │  ┌──────────────┬──────────────────────────────────────────────────┐ │ │
│  │  │ id           │ Primary Key                                       │ │ │
│  │  │ article_number│ "74"                                             │ │ │
│  │  │ title        │ "فسخ عقد العمل من قبل صاحب العمل"                │ │ │
│  │  │ content      │ Full article text                                 │ │ │
│  │  │ keywords     │ Array of keywords                                 │ │ │
│  │  │ law_source_id│ FK → law_source.id                               │ │ │
│  │  └──────────────┴──────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  law_branch (Hierarchy Level 1)                                      │ │
│  │  ┌──────────────┬──────────────────────────────────────────────────┐ │ │
│  │  │ id           │ Primary Key                                       │ │ │
│  │  │ branch_number│ "الباب الثالث"                                   │ │ │
│  │  │ branch_name  │ "إنهاء عقد العمل"                                │ │ │
│  │  │ law_source_id│ FK → law_source.id                               │ │ │
│  │  └──────────────┴──────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  law_chapter (Hierarchy Level 2)                                     │ │
│  │  ┌──────────────┬──────────────────────────────────────────────────┐ │ │
│  │  │ id           │ Primary Key                                       │ │ │
│  │  │ chapter_number│ "الفصل الأول"                                   │ │ │
│  │  │ chapter_name │ "فسخ العقد"                                      │ │ │
│  │  │ branch_id    │ FK → law_branch.id                                │ │ │
│  │  └──────────────┴──────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         AI MODEL LAYER                                     │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  Sentence Transformers                                                │ │
│  │  Model: paraphrase-multilingual-mpnet-base-v2                        │ │
│  │                                                                       │ │
│  │  Input:  "فسخ عقد العمل"                                             │ │
│  │     ↓                                                                 │ │
│  │  Tokenization                                                         │ │
│  │     ↓                                                                 │ │
│  │  [101, 1234, 5678, ..., 102]  (Token IDs)                           │ │
│  │     ↓                                                                 │ │
│  │  Transformer Model (12 layers, 768 hidden size)                      │ │
│  │     ↓                                                                 │ │
│  │  Mean Pooling                                                         │ │
│  │     ↓                                                                 │ │
│  │  Output: [0.123, -0.456, 0.789, ..., 0.234]  (768 dimensions)       │ │
│  │                                                                       │ │
│  │  Model Stats:                                                         │ │
│  │  • Parameters: 278M                                                   │ │
│  │  • Embedding Dimension: 768                                           │ │
│  │  • Max Sequence Length: 512 tokens                                   │ │
│  │  • Supports: 50+ languages including Arabic                           │ │
│  │  • Inference Time: 50-100ms (CPU), 10-20ms (GPU)                     │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow - Detailed Sequence

```
Time   Component              Action                              Data
─────────────────────────────────────────────────────────────────────────────
T+0ms  Client                POST /similar-laws                  query="فسخ عقد"
  ↓    
T+5ms  Middleware            Validate JWT Token                  user_id=123
  ↓    
T+8ms  API Route             Extract params                      top_k=10, threshold=0.7
  ↓    
T+10ms SemanticSearchService Check cache                         MISS → continue
  ↓    
T+12ms EmbeddingService      Check model loaded                  model=loaded ✓
  ↓    
T+15ms EmbeddingService      Encode query text                   "فسخ عقد" → AI Model
  ↓    
T+65ms EmbeddingService      Return embedding                    [768 floats]
  ↓    
T+70ms SemanticSearchService Build SQL query                     WHERE law_source_id IS NOT NULL
  ↓    
T+150ms Database             Execute query                       Return 600 chunks
  ↓    
T+155ms SemanticSearchService Calculate similarities (loop)      For each 600 chunks
  ↓    
T+350ms SemanticSearchService Filter by threshold                152 chunks >= 0.7
  ↓    
T+355ms SemanticSearchService Enrich metadata (loop)             Query 4 tables per chunk
  ↓    
T+850ms SemanticSearchService Sort & limit                       Top 10 results
  ↓    
T+855ms SemanticSearchService Cache results                      Store for future
  ↓    
T+860ms API Route             Format response                     JSON structure
  ↓    
T+865ms Client                Receive response                    200 OK + data
```

## 🧮 Similarity Calculation - Mathematical Detail

### Cosine Similarity Formula

```
                    A · B
similarity = ─────────────────
              ||A|| × ||B||

Where:
  A = Query embedding vector
  B = Chunk embedding vector
  · = Dot product
  ||A|| = Euclidean norm (magnitude) of A
```

### Step-by-Step Calculation

```python
# Given:
query_embedding = [0.1, 0.2, 0.3]    # Simplified 3D (actual is 768D)
chunk_embedding = [0.15, 0.19, 0.28]

# Step 1: Calculate dot product
dot_product = (0.1 × 0.15) + (0.2 × 0.19) + (0.3 × 0.28)
            = 0.015 + 0.038 + 0.084
            = 0.137

# Step 2: Calculate norms
norm_query = √(0.1² + 0.2² + 0.3²)
           = √(0.01 + 0.04 + 0.09)
           = √0.14
           = 0.374

norm_chunk = √(0.15² + 0.19² + 0.28²)
           = √(0.0225 + 0.0361 + 0.0784)
           = √0.137
           = 0.370

# Step 3: Calculate similarity
similarity = 0.137 / (0.374 × 0.370)
           = 0.137 / 0.138
           = 0.993

# Result: 99.3% similar!
```

### Boost Factors Application

```python
base_similarity = 0.85

# Apply verified boost (if admin-verified)
if chunk.verified_by_admin:
    base_similarity *= 1.1  # +10%
    # 0.85 → 0.935

# Apply recency boost (if < 30 days old)
if days_old < 30:
    base_similarity *= 1.05  # +5%
    # 0.935 → 0.982

# Cap at 1.0
final_similarity = min(base_similarity, 1.0)
# 0.982 (stays as is)
```

## 🗄️ Database Schema Relationships

```
┌─────────────────────┐
│   knowledge_chunk   │
│  ┌───────────────┐  │
│  │ id            │  │
│  │ content       │  │
│  │ embedding_vec │  │◄──────────────────────┐
│  │ law_source_id │──┼──┐                    │
│  │ article_id    │──┼──┼──┐                 │ Main table
│  │ branch_id     │──┼──┼──┼──┐              │ (where search happens)
│  │ chapter_id    │──┼──┼──┼──┼──┐           │
│  │ case_id       │  │  │  │  │  │           │
│  │ document_id   │  │  │  │  │  │           │
│  └───────────────┘  │  │  │  │  │           │
└─────────────────────┘  │  │  │  │           │
                         │  │  │  │           │
        ┌────────────────┘  │  │  │           │
        │                   │  │  │           │
        ▼                   │  │  │           │
┌─────────────────────┐     │  │  │           │
│    law_source       │     │  │  │           │
│  ┌───────────────┐  │     │  │  │           │
│  │ id            │◄─┘     │  │  │           │
│  │ name          │        │  │  │           │ Enrichment tables
│  │ type          │        │  │  │           │ (JOIN for metadata)
│  │ jurisdiction  │        │  │  │           │
│  │ issue_date    │        │  │  │           │
│  └───────────────┘  │     │  │  │           │
└─────────────────────┘     │  │  │           │
                            │  │  │           │
       ┌────────────────────┘  │  │           │
       │                       │  │           │
       ▼                       │  │           │
┌─────────────────────┐        │  │           │
│    law_article      │        │  │           │
│  ┌───────────────┐  │        │  │           │
│  │ id            │◄─┘        │  │           │
│  │ article_num   │           │  │           │
│  │ title         │           │  │           │
│  │ keywords      │           │  │           │
│  │ law_source_id │           │  │           │
│  └───────────────┘  │        │  │           │
└─────────────────────┘        │  │           │
                               │  │           │
      ┌────────────────────────┘  │           │
      │                           │           │
      ▼                           │           │
┌─────────────────────┐           │           │
│    law_branch       │           │           │
│  ┌───────────────┐  │           │           │
│  │ id            │◄─┘           │           │
│  │ branch_num    │              │           │
│  │ branch_name   │              │           │
│  │ law_source_id │              │           │
│  └───────────────┘  │           │           │
└─────────────────────┘           │           │
                                  │           │
     ┌────────────────────────────┘           │
     │                                        │
     ▼                                        │
┌─────────────────────┐                       │
│    law_chapter      │                       │
│  ┌───────────────┐  │                       │
│  │ id            │◄─┘                       │
│  │ chapter_num   │                          │
│  │ chapter_name  │                          │
│  │ branch_id     │                          │
│  └───────────────┘  │                       │
└─────────────────────┘                       │
                                              │
Search Query ─────────────────────────────────┘
(Filters chunks, then JOINs with enrichment tables)
```

## 💾 Caching Strategy

```
┌────────────────────────────────────────────────────────────────┐
│                    CACHE ARCHITECTURE                          │
└────────────────────────────────────────────────────────────────┘

1. Embedding Cache (in EmbeddingService)
   ┌──────────────────────────────────────────┐
   │ Key: Text string                         │
   │ Value: [768 float embedding]             │
   │ Max Size: 1000 entries                   │
   │ Purpose: Avoid re-encoding same text     │
   └──────────────────────────────────────────┘
   
   Example:
   _embedding_cache = {
     "فسخ عقد العمل": [0.123, -0.456, ..., 0.234],
     "حقوق العامل": [0.234, -0.567, ..., 0.345]
   }

2. Query Results Cache (in SemanticSearchService)
   ┌──────────────────────────────────────────┐
   │ Key: "laws_{query}_{top_k}_{threshold}"  │
   │ Value: List of enriched results          │
   │ Max Size: 100 queries                    │
   │ Purpose: Avoid re-searching same query   │
   └──────────────────────────────────────────┘
   
   Example:
   _query_cache = {
     "laws_فسخ عقد_10_0.7": [
       {chunk_id: 123, similarity: 0.89, ...},
       {chunk_id: 456, similarity: 0.87, ...}
     ]
   }

Cache Hit Flow:
┌───────────┐     ┌──────────┐     ┌───────────┐
│  Request  │────→│ Check    │────→│  Return   │
│  (20ms)   │     │  Cache   │ HIT │  Cached   │
└───────────┘     └──────────┘     └───────────┘

Cache Miss Flow:
┌───────────┐     ┌──────────┐     ┌────────────┐     ┌─────────┐
│  Request  │────→│ Check    │ MISS│  Full      │────→│ Cache & │
│  (500ms+) │     │  Cache   │────→│  Search    │     │ Return  │
└───────────┘     └──────────┘     └────────────┘     └─────────┘
```

## 🔧 Configuration & Settings

```python
# Location: app/services/embedding_service.py
class EmbeddingService:
    # Model selection
    MODELS = {
        'default': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        'large': 'intfloat/multilingual-e5-large',
        'small': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    }
    
    # Performance settings
    batch_size = 32              # Process 32 chunks at once
    max_seq_length = 512         # Max tokens per text
    
    # Cache settings
    _cache_max_size = 1000       # Max 1000 embeddings cached
    
    # Device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'


# Location: app/services/semantic_search_service.py
class SemanticSearchService:
    # Cache settings
    cache_enabled = True
    _cache_max_size = 100        # Max 100 query results cached
    
    # Boost factors
    VERIFIED_BOOST = 1.1         # +10% for verified content
    RECENCY_BOOST = 1.05         # +5% for recent content
    RECENCY_THRESHOLD_DAYS = 30  # Apply boost if < 30 days old
```

## 📊 Performance Benchmarks

```
┌─────────────────────────────────────────────────────────────┐
│                    RESPONSE TIME BREAKDOWN                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Authentication              ▌ 10ms                         │
│  Input Validation            ▌ 5ms                          │
│  Cache Check                 ▌ 2ms                          │
│  Query Embedding             ████ 50-100ms                  │
│  Database Query              █████ 50-200ms                 │
│  Similarity Calculation      ████████████ 200-800ms         │
│  Result Enrichment           ██████████ 100-500ms           │
│  Sorting & Limiting          ▌ 5ms                          │
│  Response Formatting         ▌ 5ms                          │
│                                                             │
│  TOTAL (No Cache):           ██████████████ 500-2000ms     │
│  TOTAL (With Cache):         ▌ ~20ms                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Optimization Factors:
┌─────────────────────────┬──────────┬──────────────────────┐
│ Factor                  │ Impact   │ How                  │
├─────────────────────────┼──────────┼──────────────────────┤
│ Cache Hit               │ -95%     │ Avoid recomputation  │
│ Add Filters             │ -40%     │ Fewer chunks         │
│ Lower top_k             │ -30%     │ Less enrichment      │
│ Higher threshold        │ -20%     │ Fewer results        │
│ Use GPU                 │ -70%     │ Faster embeddings    │
│ Database Indexes        │ -50%     │ Faster queries       │
└─────────────────────────┴──────────┴──────────────────────┘
```

---

**Last Updated**: October 9, 2025
**Version**: 1.0
**Document Type**: Technical Architecture

