# 🤖 Embedding Scripts - Simple Guide

**Only 4 Essential Scripts Remain!**

---

## 📂 What's in This Folder

| # | Script | Purpose | When to Use |
|---|--------|---------|-------------|
| **1** | `generate_embeddings_batch.py` | **Main script** - Generate embeddings for NEW chunks only | After uploading new laws (daily use) |
| **2** | `regenerate_embeddings.py` | Regenerate ALL embeddings (overwrite existing) | After model update or content changes (rare) |
| **3** | `check_embedding_quality.py` | Check quality of embeddings | To verify embeddings are good |
| **4** | `check_embedding_dimension.py` | Check embedding dimensions | To verify correct dimensions (768) |

---

## 🎯 Most Important Script

### **`generate_embeddings_batch.py`** ← START HERE!

This is the **main script** you'll use 99% of the time.

**Simple Usage**:
```bash
# Generate embeddings for all chunks that don't have them yet
python scripts/generate_embeddings_batch.py --pending

# Check how many chunks need embeddings
python scripts/generate_embeddings_batch.py --status
```

---

## 🔄 Complete Flow (Simple)

```
1. Upload Law PDF via API
      ↓
2. Law gets parsed into chunks
   (chunks have no embeddings yet)
      ↓
3. Run: python scripts/generate_embeddings_batch.py --pending
      ↓
4. Script finds chunks without embeddings
      ↓
5. AI Model loads (768-dimensional BERT)
      ↓
6. For each chunk:
   Text → AI Model → [768 numbers]
      ↓
7. Save embeddings to database
      ↓
8. ✅ Done! Chunks now searchable
```

---

## 📖 How to Follow the Code

### **Step 1: Read the Main Script**

Open: `scripts/generate_embeddings_batch.py`

**Key Parts**:
```python
Line 66-111:   class BatchEmbeddingGenerator
Line 98:       self.embedding_service = EmbeddingService(db)
Line 170-247:  async def process_pending_chunks()  ← Main function
Line 220:      result = await embedding_service.generate_batch_embeddings()
```

### **Step 2: Follow to Service Layer**

The script calls: `app/services/arabic_legal_embedding_service.py`

**Key Parts**:
```python
Line 32:       class ArabicLegalEmbeddingService
Line 151:      def initialize_model()  ← Loads AI model
Line 217:      def encode_text()  ← Converts text to embedding
Line 339:      async def generate_batch_embeddings()  ← Main processing
```

### **Step 3: Understand the Model**

The service uses: `SentenceTransformer` from Hugging Face

**Model**: `paraphrase-multilingual-mpnet-base-v2`
- Input: Text (any language)
- Output: 768 numbers
- Speed: 8-12 chunks/second (CPU)

---

## 💡 Simple Example

```bash
# 1. Check status
python scripts/generate_embeddings_batch.py --status

# Output:
# 📊 SYSTEM STATUS
# 📦 Total chunks: 100
# ✅ With embeddings: 50
# ⏳ Without embeddings: 50
# 📈 Completion: 50.00%

# 2. Generate embeddings
python scripts/generate_embeddings_batch.py --pending

# Output:
# 🚀 Starting PENDING chunks embedding generation
# 📦 Found 50 pending chunks
# 🤖 Initializing model...
# ⚙️  Processing batch 1/1
# ✅ Batch processing complete: 50 successful, 0 failed
# ⏱️  Duration: 5.8 seconds
# ⚡ Speed: 8.6 chunks/sec

# 3. Verify
python scripts/generate_embeddings_batch.py --status

# Output:
# 📦 Total chunks: 100
# ✅ With embeddings: 100  ← All done!
# 📈 Completion: 100.00%
```

---

## 🎓 Code Reading Order

**To understand how embeddings work, read in this order**:

1. **`scripts/generate_embeddings_batch.py`** (lines 170-247)
   - See how chunks are found and processed

2. **`app/services/arabic_legal_embedding_service.py`** (lines 339-431)
   - See how batch processing works

3. **`app/services/arabic_legal_embedding_service.py`** (lines 217-292)
   - See how text becomes numbers

---

## 🔍 What Each Script Does

### 1. **generate_embeddings_batch.py**
```python
# What it does:
1. Connects to database
2. Finds chunks without embeddings
3. Calls embedding service
4. Reports statistics

# Key function:
async def process_pending_chunks():
    # Get chunks where embedding_vector IS NULL
    chunks = await db.execute(query)
    
    # Generate embeddings
    result = await embedding_service.generate_batch_embeddings(chunk_ids)
    
    # Print report
    print(f"Processed: {result['processed_chunks']}")
```

### 2. **regenerate_embeddings.py**
```python
# What it does:
1. Finds ALL chunks (even with embeddings)
2. Regenerates embeddings with new/updated model
3. Tests search functionality

# When to use:
- After switching to different model
- After updating chunk content
- To fix corrupted embeddings
```

### 3. **check_embedding_quality.py**
```python
# What it does:
1. Checks if embeddings exist
2. Verifies dimension (should be 768)
3. Tests similarity calculations

# Use to verify everything is working correctly
```

### 4. **check_embedding_dimension.py**
```python
# What it does:
1. Reads embeddings from database
2. Checks if dimension is correct (768)
3. Reports any issues

# Quick verification tool
```

---

## 🚀 Quick Commands

```bash
# Most common: Generate embeddings for new chunks
python scripts/generate_embeddings_batch.py --pending

# Check status before generating
python scripts/generate_embeddings_batch.py --status

# Process specific document only
python scripts/generate_embeddings_batch.py --document-id 5

# Regenerate all embeddings (use carefully!)
python scripts/regenerate_embeddings.py

# Check quality
python scripts/check_embedding_quality.py

# Check dimensions
python scripts/check_embedding_dimension.py
```

---

## ✅ Summary

**You now have only 4 scripts**:
1. ✅ `generate_embeddings_batch.py` ← Use this 99% of the time
2. ✅ `regenerate_embeddings.py` ← Use when updating model
3. ✅ `check_embedding_quality.py` ← Use to verify
4. ✅ `check_embedding_dimension.py` ← Use to verify

**All test and utility scripts have been removed!**

**Start reading from**:
- `scripts/generate_embeddings_batch.py` (line 170)
- Then go to: `app/services/arabic_legal_embedding_service.py` (line 339)

---

**Created**: October 9, 2025  
**Purpose**: Simple guide to embedding scripts  
**Status**: Only essential scripts remain ✅

