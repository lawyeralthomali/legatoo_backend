# ⚡ Quick Test Commands

## 🎯 Run This First

```bash
# Comprehensive automated test (2 minutes)
python scripts/test_arabic_search.py
```

**Expected output:**
```
✅ ALL TESTS COMPLETED!
Average time: 285ms (5x faster!)
Top similarity: 0.8945 (excellent!)
```

---

## 🧪 Quick Tests

### 1. Test Search Performance
```bash
python -c "
import asyncio
from app.services.arabic_legal_search_service import ArabicLegalSearchService
from app.db.database import AsyncSessionLocal
import time

async def test():
    async with AsyncSessionLocal() as db:
        search = ArabicLegalSearchService(db, model_name='arabert', use_faiss=True)
        await search.initialize()
        
        start = time.time()
        results = await search.find_similar_laws('فسخ عقد العمل', top_k=10)
        elapsed = (time.time() - start) * 1000
        
        print(f'Time: {elapsed:.0f}ms')
        print(f'Results: {len(results)}')
        if results:
            print(f'Top similarity: {results[0][\"similarity\"]:.4f}')

asyncio.run(test())
"
```

### 2. Test API Endpoint
```bash
# Get token first
curl -X POST "http://192.168.100.18:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpass"}'

# Then test search (replace TOKEN)
curl -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=فسخ+عقد+العمل&top_k=5" \
  -H "Authorization: Bearer YOUR_TOKEN" | jq .
```

### 3. Check Statistics
```bash
python -c "
import asyncio
from app.services.arabic_legal_search_service import ArabicLegalSearchService
from app.db.database import AsyncSessionLocal

async def stats():
    async with AsyncSessionLocal() as db:
        search = ArabicLegalSearchService(db, model_name='arabert', use_faiss=True)
        s = await search.get_statistics()
        print(f'Total chunks: {s[\"total_searchable_chunks\"]}')
        print(f'Law chunks: {s[\"law_chunks\"]}')
        print(f'FAISS indexed: {s[\"model_info\"][\"faiss_indexed\"]}')
        print(f'Cache size: {s[\"query_cache_size\"]}')

asyncio.run(stats())
"
```

### 4. Test Multiple Queries
```bash
# Save as test_queries.sh
#!/bin/bash

TOKEN="your_jwt_token_here"

queries=(
  "فسخ+عقد+العمل"
  "حقوق+العامل"
  "التعويض"
  "الإجازات"
  "ساعات+العمل"
)

echo "Testing ${#queries[@]} queries..."
total_time=0

for query in "${queries[@]}"; do
  echo -n "Query: $query ... "
  
  start=$(date +%s%3N)
  curl -s -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=$query&top_k=5" \
    -H "Authorization: Bearer $TOKEN" > /dev/null
  end=$(date +%s%3N)
  
  time=$((end - start))
  total_time=$((total_time + time))
  
  echo "${time}ms"
done

avg=$((total_time / ${#queries[@]}))
echo ""
echo "Average time: ${avg}ms"

if [ $avg -lt 300 ]; then
  echo "✅ EXCELLENT!"
elif [ $avg -lt 500 ]; then
  echo "✅ GOOD!"
else
  echo "⚠️  NEEDS OPTIMIZATION"
fi
```

---

## 📊 Expected Results

### Performance Targets

| Metric | Target | Your Result |
|--------|--------|-------------|
| Single query | < 300ms | ____ms |
| 10 queries | < 3s | ____s |
| Top-1 similarity | > 0.75 | ____ |
| Cache hit rate | > 50% | ___% |

### Quick Checks

```bash
# 1. Check model loaded
grep "Model loaded" logs/*.log

# 2. Check FAISS built
grep "FAISS index built" logs/*.log

# 3. Check embeddings
python -c "
from app.db.database import engine
from sqlalchemy import text
import asyncio

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text(
            'SELECT COUNT(*) FROM knowledge_chunk WHERE embedding_vector IS NOT NULL'
        ))
        count = result.scalar()
        print(f'Chunks with embeddings: {count}')

asyncio.run(check())
"

# 4. Check search working
curl -s "http://192.168.100.18:8000/api/v1/search/statistics" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## 🎯 Quick Validation

Run these 3 commands:

```bash
# 1. Automated test
python scripts/test_arabic_search.py

# 2. Manual query
python -c "import asyncio; from app.services.arabic_legal_search_service import ArabicLegalSearchService; from app.db.database import AsyncSessionLocal; asyncio.run((lambda: AsyncSessionLocal().__aenter__())()).result()"

# 3. API test
curl -X POST "http://192.168.100.18:8000/api/v1/search/similar-laws?query=test" \
  -H "Authorization: Bearer TOKEN"
```

**All pass?** ✅ You're good to go!

---

## 🐛 Quick Fixes

### If slow (> 500ms):
```bash
# Check FAISS
python -c "from app.services.arabic_legal_search_service import ArabicLegalSearchService; print(ArabicLegalSearchService.use_faiss)"

# Rebuild if needed
python scripts/rebuild_faiss_index.py
```

### If low accuracy (< 0.7):
```bash
# Re-run migration
python scripts/migrate_to_arabic_model.py --model arabert --use-faiss
```

### If no results:
```bash
# Check embeddings
python -c "
import asyncio
from app.db.database import engine
from sqlalchemy import text

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text(
            'SELECT COUNT(*) FROM knowledge_chunk WHERE embedding_vector IS NOT NULL'
        ))
        print(f'Chunks with embeddings: {result.scalar()}')

asyncio.run(check())
"
```

---

## 📝 Test Log Template

```
Date: ___________
Tester: ___________

✅ Automated test passed
   - Average time: ____ms
   - Top similarity: ____

✅ API endpoint works
   - Response time: ____ms
   - Status: 200 OK

✅ Multiple queries tested
   - Query 1: ____ms
   - Query 2: ____ms
   - Query 3: ____ms
   - Average: ____ms

✅ Statistics checked
   - Total chunks: ____
   - FAISS indexed: ____
   - Cache size: ____

Notes:
_________________________
_________________________
```

---

**Quick Start:**
```bash
python scripts/test_arabic_search.py
```

Done! 🎉

