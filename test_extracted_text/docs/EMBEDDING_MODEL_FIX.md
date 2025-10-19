# 🚨 CRITICAL ISSUE: Wrong Model Type

## Problem Identified

The system is using **raw BERT models** (`AutoModel` from transformers) instead of **Sentence Transformers**!

### Why This Is Wrong:

1. **Base BERT models** (like `aubmindlab/bert-base-arabertv2`) are designed for:
   - Token classification
   - Masked language modeling
   - NOT for sentence embeddings!

2. **Sentence Transformers** are specifically fine-tuned for:
   - Semantic similarity
   - Sentence embeddings
   - Information retrieval

### Evidence:

- "تزوير طابع" vs "شراء سيارة" (completely different topics):
  - Current similarity: **0.6369** ❌ (should be < 0.3)
  
- Query "عقوبة تزوير الطوابع" vs Chunk about stamp forgery:
  - Current similarity: **0.3172** ❌ (should be > 0.85)

##  Solution

### Option 1: Use Arabic Sentence Transformer (RECOMMENDED)

```python
from sentence_transformers import SentenceTransformer

# Best Arabic models for sentence similarity:
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
# OR
model = SentenceTransformer('sentence-transformers/LaBSE')  # Language-agnostic BERT
```

### Option 2: Use Arabic-specific Sentence Transformer

```bash
# Check if available:
# - 'aubmindlab/arabert-sentence-transformers'
# - 'sentence-transformers/distiluse-base-multilingual-cased-v1'
```

### Option 3: Fine-tune AraBERT for Sentence Similarity

This requires training data and time - not practical for immediate fix.

---

## Immediate Fix Needed

**Change the model initialization from:**

```python
from transformers import AutoTokenizer, AutoModel

self.tokenizer = AutoTokenizer.from_pretrained(model_path)
self.model = AutoModel.from_pretrained(model_path)
```

**To:**

```python
from sentence_transformers import SentenceTransformer

self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
```

---

## Testing After Fix

Run:
```bash
py scripts/test_model_sanity.py
```

**Expected results:**
- ✅ Identical text: similarity = 1.0000
- ✅ Similar text: similarity > 0.80
- ✅ Different text: similarity < 0.30

---

## Why This Wasn't Caught Earlier

1. The embeddings had correct dimension (768)
2. The code compiled without errors
3. We checked for embeddings existence, not quality
4. The validation tests in migration script didn't check similarity scores

---

## Impact

This issue affects **ALL search results** since system launch. The search is essentially random because the embeddings don't properly capture semantic meaning.

**Priority:** 🔴 CRITICAL - Must fix immediately

---

## Next Steps

1. Update `ArabicLegalEmbeddingService` to use `SentenceTransformer`
2. Re-run embedding generation with correct model
3. Test search accuracy
4. Update requirements.txt if needed


