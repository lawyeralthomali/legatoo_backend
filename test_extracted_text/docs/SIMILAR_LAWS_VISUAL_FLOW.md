# 🎨 Visual Flow Diagram: `/api/v1/search/similar-laws`

**Created**: October 9, 2025  
**Purpose**: Visual representation of the complete search flow

---

## 🌊 Complete Request-Response Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         👤 USER/CLIENT APPLICATION                          │
│                                                                             │
│  🔍 Search Query: "فسخ عقد العمل"                                           │
│  📊 Parameters: top_k=10, threshold=0.7                                     │
│  🔐 Auth: JWT Token                                                         │
│                                                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ HTTP POST Request
                                │ /api/v1/search/similar-laws
                                │ Authorization: Bearer <token>
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    🚪 STEP 1: API GATEWAY & MIDDLEWARE                      │
│                    File: app/routes/search_router.py                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  1.1 🔐 JWT Authentication (get_current_user)                        │ │
│  │      ├─ Extract token from header                                    │ │
│  │      ├─ Verify signature                                             │ │
│  │      ├─ Check expiration                                             │ │
│  │      └─ Extract user_id: "user123"                                   │ │
│  │                                                                       │ │
│  │  1.2 ✅ Input Validation (FastAPI)                                   │ │
│  │      ├─ query: min 3 chars ✓                                         │ │
│  │      ├─ top_k: 1-100 ✓                                               │ │
│  │      ├─ threshold: 0.0-1.0 ✓                                         │ │
│  │      └─ Optional filters ✓                                           │ │
│  │                                                                       │ │
│  │  1.3 📦 Build Filter Dictionary                                      │ │
│  │      filters = {                                                     │ │
│  │        'jurisdiction': jurisdiction,                                 │ │
│  │        'law_source_id': law_source_id                                │ │
│  │      }                                                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ Call Service Layer
                                │ search_service.find_similar_laws(...)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│               🧠 STEP 2: SEARCH SERVICE (Main Logic)                        │
│               File: app/services/arabic_legal_search_service.py             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  2.1 💾 Check Cache                                                  │ │
│  │      cache_key = "laws_فسخ عقد العمل_10_0.7_None"                   │ │
│  │                                                                       │ │
│  │      if cache_key in _query_cache:                                   │ │
│  │          🎯 CACHE HIT! Return instantly (20ms)                       │ │
│  │          └─ Skip to Step 9                                           │ │
│  │                                                                       │ │
│  │      else:                                                            │ │
│  │          ❌ CACHE MISS - Continue to next step                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  2.2 🤖 Call Embedding Service                                       │ │
│  │      query_embedding = embedding_service.encode_text(query)          │ │
│  │      ↓                                                                │ │
│  │      Go to STEP 3 ──────────────────────────────────────────────────→│ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│               🧬 STEP 3: EMBEDDING SERVICE (AI Processing)                  │
│               File: app/services/arabic_legal_embedding_service.py          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  3.1 💾 Check Embedding Cache                                        │ │
│  │      if "فسخ عقد العمل" in _embedding_cache:                         │ │
│  │          Return cached embedding (instant)                           │ │
│  │      else:                                                            │ │
│  │          Continue to AI model                                        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  3.2 🔧 Ensure Model is Loaded                                       │ │
│  │      if model is None:                                               │ │
│  │          Load paraphrase-multilingual-mpnet-base-v2                  │ │
│  │          (278M parameters, 768 dimensions)                           │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  3.3 ✂️ Truncate Text if Needed                                      │ │
│  │      max_length = 512 tokens (~2048 chars)                           │ │
│  │      if len(text) > max_length:                                      │ │
│  │          text = text[:max_length]                                    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  3.4 🤖 Generate Embedding with AI Model                             │ │
│  │                                                                       │ │
│  │      Input: "فسخ عقد العمل"                                          │ │
│  │         ↓                                                             │ │
│  │      Tokenization                                                     │ │
│  │         ↓                                                             │ │
│  │      [101, 1234, 5678, ..., 102]  (Token IDs)                       │ │
│  │         ↓                                                             │ │
│  │      Transformer Model (12 layers, 768 hidden)                       │ │
│  │         ↓                                                             │ │
│  │      Mean Pooling                                                     │ │
│  │         ↓                                                             │ │
│  │      Output: [0.123, -0.456, 0.789, ..., 0.234]                     │ │
│  │              └────────────────────────────────┘                       │ │
│  │                     768 dimensions                                    │ │
│  │                                                                       │ │
│  │      Time: 50-100ms (CPU), 10-20ms (GPU)                            │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  3.5 💾 Cache & Return                                               │ │
│  │      _embedding_cache["فسخ عقد العمل"] = embedding                   │ │
│  │      return embedding                                                 │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ Return query_embedding
                                │ [768 floats]
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│               📊 STEP 4: DATABASE QUERY                                     │
│               File: app/services/arabic_legal_search_service.py             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  4.1 🔨 Build SQL Query                                              │ │
│  │                                                                       │ │
│  │      SELECT * FROM knowledge_chunk                                   │ │
│  │      WHERE embedding_vector IS NOT NULL                              │ │
│  │        AND embedding_vector != ''                                    │ │
│  │        AND law_source_id IS NOT NULL                                 │ │
│  │        [+ jurisdiction filter if provided]                           │ │
│  │        [+ law_source_id filter if provided]                          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  4.2 💾 Execute Query                                                │ │
│  │      result = await db.execute(query_builder)                        │ │
│  │      chunks = result.scalars().all()                                 │ │
│  │                                                                       │ │
│  │      📊 Found 600 law chunks with embeddings                         │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ Return chunks[]
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│               🧮 STEP 5: CALCULATE SIMILARITIES                             │
│               File: app/services/arabic_legal_search_service.py             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  5.1 🔁 Loop Through All Chunks                                      │ │
│  │                                                                       │ │
│  │      for chunk in chunks:  # 600 iterations                          │ │
│  │                                                                       │ │
│  │          # Parse stored embedding                                    │ │
│  │          chunk_embedding = json.loads(chunk.embedding_vector)        │ │
│  │          chunk_embedding = np.array(chunk_embedding)                 │ │
│  │          # [0.15, -0.48, 0.82, ..., 0.27]  (768 floats)             │ │
│  │                                                                       │ │
│  │          # Calculate cosine similarity                               │ │
│  │          base_similarity = cosine_similarity(                        │ │
│  │              query_embedding,    # [768 floats]                      │ │
│  │              chunk_embedding     # [768 floats]                      │ │
│  │          )                                                            │ │
│  │                                                                       │ │
│  │          ┌────────────────────────────────────────────┐              │ │
│  │          │  Cosine Similarity Formula:                │              │ │
│  │          │                                             │              │ │
│  │          │              A · B                          │              │ │
│  │          │  similarity = ─────────────                │              │ │
│  │          │              ||A|| × ||B||                 │              │ │
│  │          │                                             │              │ │
│  │          │  Where:                                     │              │ │
│  │          │  A = Query embedding (768D)                │              │ │
│  │          │  B = Chunk embedding (768D)                │              │ │
│  │          │  · = Dot product                            │              │ │
│  │          │  ||A|| = Euclidean norm of A               │              │ │
│  │          │                                             │              │ │
│  │          │  Example:                                   │              │ │
│  │          │  dot_product = 0.137                        │              │ │
│  │          │  norm_A = 0.374                             │              │ │
│  │          │  norm_B = 0.370                             │              │ │
│  │          │  similarity = 0.137/(0.374×0.370) = 0.993  │              │ │
│  │          │  Result: 99.3% similar!                     │              │ │
│  │          └────────────────────────────────────────────┘              │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  5.2 🚀 Apply Boost Factors                                          │ │
│  │                                                                       │ │
│  │      score = base_similarity  # 0.85                                 │ │
│  │                                                                       │ │
│  │      # Verified boost (+15%)                                         │ │
│  │      if chunk.verified_by_admin:                                     │ │
│  │          score *= 1.15  # 0.85 → 0.9775                             │ │
│  │                                                                       │ │
│  │      # Recency boost (+10% if < 90 days old)                        │ │
│  │      if days_old < 90:                                               │ │
│  │          score *= 1.10  # 0.9775 → 1.07525                          │ │
│  │                                                                       │ │
│  │      # Cap at 1.0                                                    │ │
│  │      final_score = min(score, 1.0)  # 1.0                           │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  5.3 🎯 Filter by Threshold                                          │ │
│  │                                                                       │ │
│  │      if final_score >= threshold:  # 0.7                             │ │
│  │          results.append(chunk)                                       │ │
│  │                                                                       │ │
│  │      📊 Result: 152 chunks passed threshold                          │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ results[] (152 chunks)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│               ✨ STEP 6: ENRICH RESULTS WITH METADATA                       │
│               File: app/services/arabic_legal_search_service.py             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  6.1 🔁 For Each Result                                              │ │
│  │                                                                       │ │
│  │      for chunk in results:                                           │ │
│  │                                                                       │ │
│  │          enriched = {                                                │ │
│  │              'chunk_id': chunk.id,                                   │ │
│  │              'content': chunk.content,                               │ │
│  │              'similarity': round(score, 4),                          │ │
│  │              'source_type': 'law',                                   │ │
│  │              'verified': chunk.verified_by_admin                     │ │
│  │          }                                                            │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  6.2 📚 Fetch Law Source Metadata                                    │ │
│  │                                                                       │ │
│  │      law_source = await db.execute(                                  │ │
│  │          SELECT * FROM law_sources                                   │ │
│  │          WHERE id = chunk.law_source_id                              │ │
│  │      )                                                                │ │
│  │                                                                       │ │
│  │      enriched['law_metadata'] = {                                    │ │
│  │          'law_id': law.id,                                           │ │
│  │          'law_name': "نظام العمل السعودي",                           │ │
│  │          'law_type': "law",                                          │ │
│  │          'jurisdiction': "المملكة العربية السعودية",                 │ │
│  │          'issue_date': "1426-08-23"                                  │ │
│  │      }                                                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  6.3 📄 Fetch Article Metadata                                       │ │
│  │                                                                       │ │
│  │      article = await db.execute(                                     │ │
│  │          SELECT * FROM law_articles                                  │ │
│  │          WHERE id = chunk.article_id                                 │ │
│  │      )                                                                │ │
│  │                                                                       │ │
│  │      enriched['article_metadata'] = {                                │ │
│  │          'article_id': article.id,                                   │ │
│  │          'article_number': "74",                                     │ │
│  │          'title': "فسخ عقد العمل من قبل صاحب العمل",                 │ │
│  │          'keywords': ["فسخ", "عقد", "عمل"]                           │ │
│  │      }                                                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  6.4 🌳 Fetch Hierarchy (Branch & Chapter)                           │ │
│  │                                                                       │ │
│  │      branch = await db.execute(...)                                  │ │
│  │      chapter = await db.execute(...)                                 │ │
│  │                                                                       │ │
│  │      enriched['branch_metadata'] = {                                 │ │
│  │          'branch_number': "الخامس",                                  │ │
│  │          'branch_name': "علاقات العمل"                               │ │
│  │      }                                                                │ │
│  │                                                                       │ │
│  │      enriched['chapter_metadata'] = {                                │ │
│  │          'chapter_number': "الثالث",                                 │ │
│  │          'chapter_name': "إنهاء عقد العمل"                           │ │
│  │      }                                                                │ │
│  │                                                                       │ │
│  │      ┌─────────────────────────────────────────┐                     │ │
│  │      │  Hierarchical Structure:                │                     │ │
│  │      │                                          │                     │ │
│  │      │  LawSource (نظام العمل السعودي)        │                     │ │
│  │      │    └─ Branch (الباب الخامس)             │                     │ │
│  │      │        └─ Chapter (الفصل الثالث)        │                     │ │
│  │      │            └─ Article (المادة 74)       │                     │ │
│  │      │                └─ Chunk (النص)          │                     │ │
│  │      └─────────────────────────────────────────┘                     │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ enriched_results[] (152 chunks)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│               🎯 STEP 7: SORT, LIMIT & CACHE                                │
│               File: app/services/arabic_legal_search_service.py             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  7.1 📊 Sort by Similarity (Descending)                              │ │
│  │                                                                       │ │
│  │      enriched_results.sort(                                          │ │
│  │          key=lambda x: x['similarity'],                              │ │
│  │          reverse=True                                                 │ │
│  │      )                                                                │ │
│  │                                                                       │ │
│  │      Results:                                                         │ │
│  │      1. similarity: 0.9345                                           │ │
│  │      2. similarity: 0.9123                                           │ │
│  │      3. similarity: 0.8987                                           │ │
│  │      ...                                                              │ │
│  │      152. similarity: 0.7001                                         │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  7.2 ✂️ Limit to top_k                                               │ │
│  │                                                                       │ │
│  │      final_results = enriched_results[:top_k]  # [:10]               │ │
│  │                                                                       │ │
│  │      📊 Result: Top 10 results                                       │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  7.3 💾 Cache Results                                                │ │
│  │                                                                       │ │
│  │      cache_key = "laws_فسخ عقد العمل_10_0.7_None"                   │ │
│  │      _query_cache[cache_key] = final_results                         │ │
│  │                                                                       │ │
│  │      💡 Next time this query comes:                                  │ │
│  │         - Skip Steps 3-7                                             │ │
│  │         - Return immediately in ~20ms                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ Return final_results
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│               📦 STEP 8: FORMAT API RESPONSE                                │
│               File: app/routes/search_router.py                             │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  8.1 🎨 Build Response Data                                          │ │
│  │                                                                       │ │
│  │      response_data = {                                               │ │
│  │          "query": "فسخ عقد العمل",                                   │ │
│  │          "results": final_results,  # Array of 10 items              │ │
│  │          "total_results": 10,                                        │ │
│  │          "threshold": 0.7                                            │ │
│  │      }                                                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  8.2 ✅ Create Success Response                                      │ │
│  │                                                                       │ │
│  │      return create_success_response(                                 │ │
│  │          message="Found 10 similar laws",                            │ │
│  │          data=response_data                                          │ │
│  │      )                                                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                │ HTTP 200 OK
                                │ Content-Type: application/json
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         📱 STEP 9: CLIENT RECEIVES RESPONSE                 │
│                                                                             │
│  {                                                                          │
│    "success": true,                                                         │
│    "message": "Found 10 similar laws",                                      │
│    "data": {                                                                │
│      "query": "فسخ عقد العمل",                                              │
│      "results": [                                                           │
│        {                                                                    │
│          "chunk_id": 123,                                                   │
│          "content": "المادة 74: يجوز لصاحب العمل فسخ العقد...",              │
│          "similarity": 0.9345,                                              │
│          "source_type": "law",                                              │
│          "verified": true,                                                  │
│          "law_metadata": {                                                  │
│            "law_name": "نظام العمل السعودي",                                │
│            "law_type": "law",                                               │
│            "jurisdiction": "المملكة العربية السعودية"                       │
│          },                                                                 │
│          "article_metadata": {                                              │
│            "article_number": "74",                                          │
│            "title": "فسخ عقد العمل من قبل صاحب العمل"                      │
│          },                                                                 │
│          "branch_metadata": { ... },                                        │
│          "chapter_metadata": { ... }                                        │
│        }                                                                    │
│        // ... 9 more results                                                │
│      ],                                                                     │
│      "total_results": 10,                                                   │
│      "threshold": 0.7                                                       │
│    },                                                                       │
│    "errors": []                                                             │
│  }                                                                          │
│                                                                             │
│  ⏱️  Total Time:                                                            │
│      First Request: 500-2000ms                                              │
│      Cached Request: ~20ms                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Points Summary

### Step 1: API Gateway (10ms)
- ✅ JWT authentication
- ✅ Parameter validation
- ✅ Build filters

### Step 2: Check Cache (2ms)
- 💾 Cache hit? → Return instantly (20ms total)
- ❌ Cache miss? → Continue to Step 3

### Step 3: Generate Query Embedding (50-100ms)
- 🤖 Use AI model (768-dimensional BERT)
- 💾 Cache embedding for future use
- 📊 Output: [768 float numbers]

### Step 4: Database Query (50-200ms)
- 📊 Get all law chunks with embeddings
- 🎯 Apply filters if provided
- 📦 Result: 600 chunks

### Step 5: Calculate Similarities (200-800ms)
- 🧮 Cosine similarity for each chunk
- 🚀 Apply boost factors (verified +15%, recent +10%)
- 🎯 Filter by threshold (≥ 0.7)
- 📊 Result: 152 matching chunks

### Step 6: Enrich with Metadata (100-500ms)
- 📚 Fetch law source info
- 📄 Fetch article details
- 🌳 Fetch hierarchy (branch, chapter)
- ✨ Build complete result objects

### Step 7: Sort, Limit & Cache (5ms)
- 📊 Sort by similarity (descending)
- ✂️ Limit to top_k (10 results)
- 💾 Cache for future queries

### Step 8: Format Response (5ms)
- 🎨 Build standardized JSON
- ✅ Success response
- 📦 Return to client

### Step 9: Client Receives (Network time)
- 📱 HTTP 200 OK
- 📦 Complete results with all metadata
- 🎉 Ready to display!

---

## 📊 Performance Timeline

```
Time    Component                  Action                    Duration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T+0ms   Client                    Send Request              -
T+10ms  API Gateway               Authenticate & Validate   10ms
T+12ms  Search Service            Check Cache               2ms (MISS)
T+15ms  Embedding Service         Check Embedding Cache     3ms (MISS)
T+65ms  AI Model                  Generate Embedding        50ms
T+70ms  Search Service            Build Database Query      5ms
T+220ms Database                  Execute Query             150ms
T+820ms Search Service            Calculate Similarities    600ms
T+1220ms Database                 Enrich Metadata           400ms
T+1225ms Search Service           Sort & Limit              5ms
T+1230ms Search Service           Cache Results             5ms
T+1235ms API Gateway              Format Response           5ms
T+1240ms Client                   Receive Response          -
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOTAL TIME: 1240ms (First Request)
```

```
Time    Component                  Action                    Duration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T+0ms   Client                    Send Request              -
T+10ms  API Gateway               Authenticate & Validate   10ms
T+12ms  Search Service            Check Cache               2ms (HIT!)
T+15ms  API Gateway               Format Response           3ms
T+20ms  Client                    Receive Response          -
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOTAL TIME: 20ms (Cached Request - 62x faster!)
```

---

## 🎨 Data Flow Visualization

```
┌──────────────┐
│    Query     │
│ "فسخ عقد"    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│     AI Model Transform        │
│  768-dimensional embedding    │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│   [0.123, -0.456, ..., 0.234]│ ◄─── Query Vector
└──────┬───────────────────────┘
       │
       │ Compare with
       │
       ▼
┌─────────────────────────────────────────────┐
│      Database (600 law chunks)              │
│                                             │
│  Chunk 1: [0.15, -0.48, ..., 0.27] → 0.93  │ ✅
│  Chunk 2: [0.11, -0.42, ..., 0.31] → 0.89  │ ✅
│  Chunk 3: [0.08, -0.52, ..., 0.19] → 0.76  │ ✅
│  ...                                        │
│  Chunk 600: [0.02, -0.61, ..., 0.05] → 0.45│ ❌
│                                             │
└─────────────┬───────────────────────────────┘
              │
              │ Filter (≥ 0.7)
              │
              ▼
┌────────────────────────────────┐
│   152 matching chunks           │
└────────────┬───────────────────┘
             │
             │ Enrich Metadata
             │
             ▼
┌────────────────────────────────────────────┐
│   Complete Results with Hierarchy          │
│                                            │
│   [Law → Branch → Chapter → Article → Text]│
└────────────┬───────────────────────────────┘
             │
             │ Sort & Limit (top 10)
             │
             ▼
┌────────────────────────────────┐
│     Final Response              │
│   10 best-matching laws         │
│   with complete metadata        │
└─────────────────────────────────┘
```

---

**Created**: October 9, 2025  
**Purpose**: Visual flow diagram for similar-laws endpoint  
**Companion Document**: SIMILAR_LAWS_COMPLETE_EXPLANATION.md

