# ⚡ Similar Laws Endpoint - Quick Reference Guide

## 🎯 Endpoint
```
POST http://192.168.100.18:8000/api/v1/search/similar-laws
```

## 📥 Request Example
```bash
curl -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=فسخ+عقد+العمل&top_k=10&threshold=0.7" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📊 Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER MAKES REQUEST                          │
│  POST /api/v1/search/similar-laws?query=فسخ عقد العمل              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 1: AUTHENTICATION                           │
│  ✓ Validates JWT Token                                             │
│  ✓ Extracts user identity                                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 2: INPUT VALIDATION                         │
│  ✓ Query length >= 3 characters                                    │
│  ✓ top_k between 1-100                                             │
│  ✓ threshold between 0.0-1.0                                       │
│  ✓ Build filters dictionary                                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 3: CHECK CACHE                              │
│  Cache Key: "laws_فسخ عقد العمل_10_0.7"                            │
│  ├─ HIT  ✓ → Return cached results (fast!)                        │
│  └─ MISS ✗ → Continue to next step                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│          STEP 4: GENERATE QUERY EMBEDDING                           │
│                                                                     │
│  Input Text: "فسخ عقد العمل"                                       │
│       ↓                                                             │
│  [AI Model: paraphrase-multilingual-mpnet-base-v2]                 │
│       ↓                                                             │
│  Output: [0.123, -0.456, 0.789, ..., 0.234]                       │
│          └─────────── 768 dimensions ──────────┘                   │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│          STEP 5: FETCH LAW CHUNKS FROM DATABASE                     │
│                                                                     │
│  SELECT * FROM knowledge_chunk                                      │
│  WHERE embedding_vector IS NOT NULL                                 │
│    AND law_source_id IS NOT NULL                                   │
│    [+ Optional Filters]                                            │
│                                                                     │
│  Result: 600 law chunks with embeddings                            │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│        STEP 6: CALCULATE SIMILARITY FOR EACH CHUNK                  │
│                                                                     │
│  For each of 600 chunks:                                           │
│  ┌──────────────────────────────────────────────────────┐          │
│  │ Chunk 1: [0.234, -0.567, 0.891, ..., 0.345] (768D)  │          │
│  │    ↓ Cosine Similarity                               │          │
│  │ Query:   [0.123, -0.456, 0.789, ..., 0.234] (768D)  │          │
│  │    ↓                                                 │          │
│  │ Similarity = 0.8945                                  │          │
│  │    ↓                                                 │          │
│  │ Apply Boosts:                                        │          │
│  │   ✓ Verified boost (+10%)  → 0.8945 × 1.1 = 0.9840 │          │
│  │    ↓                                                 │          │
│  │ Compare with threshold (0.7):                        │          │
│  │   0.9840 >= 0.7 ✓ PASS → Add to results            │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                     │
│  After processing all 600 chunks:                                  │
│  ├─ 152 chunks above threshold                                     │
│  └─ 448 chunks below threshold (discarded)                         │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│        STEP 7: ENRICH RESULTS WITH METADATA                         │
│                                                                     │
│  For each of 152 results:                                          │
│  ┌──────────────────────────────────────────────────────┐          │
│  │ Chunk ID: 123                                        │          │
│  │ Content: "المادة 74: يجوز لصاحب العمل فسخ..."        │          │
│  │ Similarity: 0.9840                                   │          │
│  │    ↓ JOIN with related tables                       │          │
│  │                                                      │          │
│  │ + LawSource (law_source_id = 5)                     │          │
│  │   → law_name: "نظام العمل السعودي"                  │          │
│  │   → jurisdiction: "المملكة العربية السعودية"        │          │
│  │                                                      │          │
│  │ + LawArticle (article_id = 74)                      │          │
│  │   → article_number: "74"                            │          │
│  │   → title: "فسخ عقد العمل من قبل صاحب العمل"        │          │
│  │                                                      │          │
│  │ + LawBranch (branch_id = 3)                         │          │
│  │   → branch_name: "إنهاء عقد العمل"                  │          │
│  │                                                      │          │
│  │ + LawChapter (chapter_id = 8)                       │          │
│  │   → chapter_name: "فسخ العقد"                       │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│          STEP 8: SORT AND LIMIT RESULTS                             │
│                                                                     │
│  All 152 results sorted by similarity:                             │
│  ┌──────────────────────────────────────────┐                      │
│  │ 1. Chunk 123  → 0.9840                   │                      │
│  │ 2. Chunk 456  → 0.9612                   │                      │
│  │ 3. Chunk 789  → 0.9534                   │                      │
│  │ 4. Chunk 234  → 0.9401                   │                      │
│  │ 5. Chunk 567  → 0.9289                   │                      │
│  │ 6. Chunk 890  → 0.9156                   │                      │
│  │ 7. Chunk 345  → 0.9023                   │                      │
│  │ 8. Chunk 678  → 0.8901                   │                      │
│  │ 9. Chunk 901  → 0.8787                   │                      │
│  │ 10. Chunk 234 → 0.8654   ◄── top_k = 10  │                      │
│  │ ────────────── CUTOFF ──────────────     │                      │
│  │ 11. Chunk 456 → 0.8523   (not returned)  │                      │
│  │ ...                                       │                      │
│  │ 152. Chunk 111 → 0.7001  (not returned)  │                      │
│  └──────────────────────────────────────────┘                      │
│                                                                     │
│  Final result: Top 10 chunks                                       │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│          STEP 9: CACHE RESULTS                                      │
│                                                                     │
│  Store in memory cache:                                            │
│  Key: "laws_فسخ عقد العمل_10_0.7"                                  │
│  Value: [10 enriched results]                                      │
│  TTL: Until cache is cleared or reaches 100 entries                │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│          STEP 10: FORMAT AND RETURN RESPONSE                        │
│                                                                     │
│  {                                                                  │
│    "success": true,                                                │
│    "message": "Found 10 similar laws",                             │
│    "data": {                                                       │
│      "query": "فسخ عقد العمل",                                     │
│      "results": [... 10 enriched chunks ...],                     │
│      "total_results": 10,                                          │
│      "threshold": 0.7                                              │
│    },                                                              │
│    "errors": []                                                    │
│  }                                                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔢 Cosine Similarity Explained

### Mathematical Formula:
```
similarity = (A · B) / (||A|| × ||B||)

Where:
  A = Query embedding vector (768 dimensions)
  B = Chunk embedding vector (768 dimensions)
  · = Dot product
  ||A|| = Euclidean norm of A
  ||B|| = Euclidean norm of B
```

### Example Calculation:
```python
# Simplified 3D example (actual is 768D)
query_vector = [1.0, 2.0, 3.0]
chunk_vector = [1.5, 2.1, 2.8]

# Step 1: Dot product
dot_product = (1.0 × 1.5) + (2.0 × 2.1) + (3.0 × 2.8)
            = 1.5 + 4.2 + 8.4
            = 14.1

# Step 2: Calculate norms
norm_query = sqrt(1.0² + 2.0² + 3.0²) = sqrt(14) ≈ 3.742
norm_chunk = sqrt(1.5² + 2.1² + 2.8²) = sqrt(14.5) ≈ 3.808

# Step 3: Calculate similarity
similarity = 14.1 / (3.742 × 3.808)
          = 14.1 / 14.25
          ≈ 0.989  (Very similar!)
```

## 📊 Database Query Breakdown

### Query 1: Fetch Chunks
```sql
-- Fetch all law chunks with embeddings
SELECT *
FROM knowledge_chunk
WHERE embedding_vector IS NOT NULL
  AND embedding_vector != ''
  AND law_source_id IS NOT NULL
  -- Optional filter: by law_source_id
  AND law_source_id = 5
  -- Optional filter: by jurisdiction (requires JOIN)
  AND law_source_id IN (
    SELECT id 
    FROM law_source 
    WHERE jurisdiction = 'المملكة العربية السعودية'
  );
```

### Query 2: Enrich with Law Metadata
```sql
-- For each matching chunk
SELECT ls.*
FROM law_source ls
WHERE ls.id = chunk.law_source_id;
```

### Query 3: Enrich with Article Metadata
```sql
-- For each matching chunk with article_id
SELECT la.*
FROM law_article la
WHERE la.id = chunk.article_id;
```

### Query 4: Enrich with Branch Metadata
```sql
-- For each matching chunk with branch_id
SELECT lb.*
FROM law_branch lb
WHERE lb.id = chunk.branch_id;
```

### Query 5: Enrich with Chapter Metadata
```sql
-- For each matching chunk with chapter_id
SELECT lc.*
FROM law_chapter lc
WHERE lc.id = chunk.chapter_id;
```

## 🎯 Similarity Score Interpretation

| Score Range | Interpretation | Typical Use Case |
|-------------|----------------|------------------|
| 0.95 - 1.00 | Nearly Identical | Exact matches, duplicates |
| 0.90 - 0.95 | Extremely Similar | Direct paraphrases |
| 0.85 - 0.90 | Very Similar | Same topic, different wording |
| 0.80 - 0.85 | Similar | Related concepts |
| 0.75 - 0.80 | Moderately Similar | Same domain, different aspects |
| 0.70 - 0.75 | Somewhat Similar | Loosely related |
| 0.60 - 0.70 | Weak Similarity | Tangentially related |
| < 0.60 | Not Similar | Unrelated or noise |

**Recommended Thresholds:**
- **Precise Search**: 0.80-0.85
- **General Search**: 0.70-0.75
- **Exploratory Search**: 0.60-0.65

## 📈 Performance Metrics

### Response Time Breakdown:
```
Total Response Time: ~500ms - 2000ms

├─ Authentication: 10ms
├─ Input Validation: 5ms
├─ Cache Check: 2ms (if hit, total = 17ms!)
├─ Query Embedding Generation: 50-100ms
├─ Database Query: 50-200ms
├─ Similarity Calculation: 200-800ms (depends on chunk count)
├─ Result Enrichment: 100-500ms (depends on result count)
├─ Sorting & Limiting: 5ms
└─ Response Formatting: 5ms
```

### Optimization Tips:
1. **Use Cache**: Subsequent identical queries return in ~20ms
2. **Add Filters**: Reduces chunks to process
3. **Lower top_k**: Faster enrichment
4. **Increase threshold**: Fewer results to enrich
5. **Use GPU**: Faster embedding generation (3-5x speedup)

## 🔧 Configuration

### AI Model Configuration
```python
# Location: app/services/embedding_service.py

MODELS = {
    'default': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
    'large': 'intfloat/multilingual-e5-large',
    'small': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
}

# Current active model: 'default'
# Embedding dimension: 768
# Max sequence length: 512 tokens
# Device: CPU (or CUDA if available)
```

### Cache Configuration
```python
# Location: app/services/semantic_search_service.py

cache_enabled = True
_cache_max_size = 100  # Max 100 queries cached
```

### Boost Factors
```python
# Location: app/services/semantic_search_service.py

boost_factors = {
    'verified_boost': True,    # +10% for admin-verified content
    'recency_boost': True       # +5% for content < 30 days old
}
```

## 🧪 Testing the Endpoint

### Test 1: Basic Search
```bash
curl -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=عقد+العمل&top_k=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test 2: With Filters
```bash
curl -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=حقوق+العامل&law_source_id=5&top_k=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test 3: High Precision
```bash
curl -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=فسخ+العقد&threshold=0.85&top_k=3" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test 4: Low Threshold (Exploratory)
```bash
curl -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=تعويض&threshold=0.6&top_k=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📂 Key Files

```
app/
├── routes/
│   └── search_router.py              # API endpoint definition
├── services/
│   ├── semantic_search_service.py    # Main search logic
│   └── embedding_service.py          # AI embedding generation
├── models/
│   └── legal_knowledge.py            # Database models
└── schemas/
    ├── search.py                     # Request/response schemas
    └── response.py                   # Standard API response format
```

## 🐛 Troubleshooting

### Problem: "Authentication failed"
**Solution**: 
```bash
# Get a fresh JWT token
curl -X POST "http://192.168.100.18:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "your_password"}'
```

### Problem: No results found
**Solution**:
1. Lower threshold: `threshold=0.5`
2. Check embeddings exist:
```bash
curl -X GET "http://192.168.100.18:8000/api/v1/search/statistics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Problem: Slow response
**Solution**:
1. Add filters to reduce search space
2. Reduce `top_k` value
3. Increase `threshold` value
4. Check database performance

## 📚 Related Documentation

- **Full Documentation**: `SIMILAR_LAWS_ENDPOINT_DOCUMENTATION.md`
- **Semantic Search Guide**: `docs/SEMANTIC_SEARCH_COMPLETE_GUIDE.md`
- **API Routes**: `any_files/API_ENDPOINTS_MAP.md`

---

**Last Updated**: October 9, 2025

