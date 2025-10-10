# 🤖 Understanding the Embedding Scripts

**Simple Explanation of Each Script**

---

## 📊 Two Different Approaches

### 1️⃣ **`generate_embeddings_batch.py`** (Generate NEW)
**Purpose**: Generate embeddings for chunks that DON'T have them yet

```
Before:
  Chunk 1: embedding=NULL ❌
  Chunk 2: embedding=NULL ❌
  Chunk 3: embedding=[0.123...] ✅ (already has)

After running:
  Chunk 1: embedding=[0.123...] ✅ (generated)
  Chunk 2: embedding=[0.234...] ✅ (generated)
  Chunk 3: embedding=[0.123...] ✅ (kept existing)
```

**When to use**: After uploading new laws (daily use)

---

### 2️⃣ **`regenerate_embeddings.py`** (Regenerate ALL)
**Purpose**: Regenerate embeddings for ALL chunks (overwrite existing)

```
Before:
  Chunk 1: embedding=[0.111...] ✅ (old)
  Chunk 2: embedding=[0.222...] ✅ (old)
  Chunk 3: embedding=[0.333...] ✅ (old)

After running:
  Chunk 1: embedding=[0.456...] ✅ (regenerated)
  Chunk 2: embedding=[0.567...] ✅ (regenerated)
  Chunk 3: embedding=[0.678...] ✅ (regenerated)
```

**When to use**: 
- After switching to a different AI model
- After fixing content issues
- When embeddings are corrupted

---

## 🔍 Key Difference

### `generate_embeddings_batch.py`
```python
# Finds chunks WHERE embedding_vector IS NULL
query = select(KnowledgeChunk).where(
    KnowledgeChunk.embedding_vector.is_(None)
)

# Generates embeddings (don't overwrite)
result = await embedding_service.generate_batch_embeddings(
    chunk_ids=chunk_ids,
    overwrite=False  # ← Don't touch existing embeddings
)
```

### `regenerate_embeddings.py`
```python
# Gets ALL chunks (even with embeddings)
query = select(KnowledgeChunk)

# Regenerates ALL embeddings (overwrite existing)
result = await embedding_service.generate_batch_embeddings(
    chunk_ids=chunk_ids,
    overwrite=True  # ← Overwrite ALL embeddings!
)
```

---

## 🎯 When to Use Each Script

### Use `generate_embeddings_batch.py` (99% of the time)

**Scenarios**:
- ✅ You uploaded a new law PDF
- ✅ You have new chunks without embeddings
- ✅ Daily/regular use
- ✅ Fast (only processes new chunks)

**Command**:
```bash
python scripts/generate_embeddings_batch.py --pending
```

---

### Use `regenerate_embeddings.py` (Rarely)

**Scenarios**:
- ⚠️  You changed the AI model
- ⚠️  Embeddings are corrupted or wrong
- ⚠️  You updated chunk content
- ⚠️  You want to use a better model

**Command**:
```bash
python scripts/regenerate_embeddings.py
```

**Warning**: This will regenerate ALL embeddings (slower!)

---

## 📊 Example Comparison

### Scenario: You have 100 chunks

**Database state**:
- 50 chunks WITH embeddings ✅
- 50 chunks WITHOUT embeddings ❌

### Run `generate_embeddings_batch.py --pending`:
```
📦 Found 50 pending chunks
⚙️  Processing 50 chunks...
✅ Done! (Only processed 50)
⏱️  Time: ~6 seconds
```

### Run `regenerate_embeddings.py`:
```
📊 Total chunks: 100
⚠️  This will regenerate ALL 100 embeddings!
⚙️  Processing 100 chunks...
✅ Done! (Processed all 100)
⏱️  Time: ~12 seconds
```

---

## 🔄 What Changed (Fixed Issue)

### Before (Wrong):
```python
# regenerate_embeddings.py was checking for NULL
result = await db.execute(
    select(KnowledgeChunk.id)
    .where(KnowledgeChunk.embedding_vector.is_(None))  # ❌ Only NULL
)

# Would say: "All chunks already have embeddings!"
```

### After (Fixed):
```python
# regenerate_embeddings.py now gets ALL chunks
result = await db.execute(
    select(KnowledgeChunk.id)  # ✅ ALL chunks
)

# And sets overwrite=True
result = await embedding_service.generate_batch_embeddings(
    chunk_ids=chunk_ids,
    overwrite=True  # ✅ Forces regeneration
)
```

---

## ✅ Summary

| Script | What It Does | When to Use | Speed |
|--------|--------------|-------------|-------|
| **`generate_embeddings_batch.py`** | Generate for NEW chunks only | 99% of the time | Fast |
| **`regenerate_embeddings.py`** | Regenerate ALL chunks | After model change | Slower |

**Your use case**:
- Daily use: `generate_embeddings_batch.py --pending` ✅
- Model update: `regenerate_embeddings.py` ⚠️

---

## 🚀 Quick Test

```bash
# For new chunks (daily use)
python scripts/generate_embeddings_batch.py --pending

# To regenerate ALL (after model change)
python scripts/regenerate_embeddings.py
```

---

**Now the `regenerate_embeddings.py` script truly regenerates ALL embeddings!** ✅

