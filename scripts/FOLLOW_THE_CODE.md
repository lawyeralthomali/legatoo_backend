# 📖 Follow The Code - Step by Step

**Simple Guide to Understanding Embedding Generation**

---

## 🎯 Start Here

You want to understand how embeddings are generated.  
**Follow these steps in order:**

---

## Step 1: Read the Main Script

**File**: `scripts/generate_embeddings_batch.py`

**Start at line 170** - This is the main function:

```python
# Line 170-247
async def process_pending_chunks(self):
    """Process only chunks without embeddings"""
    
    # 1. Find chunks without embeddings
    query = select(KnowledgeChunk).where(
        KnowledgeChunk.embedding_vector.is_(None)
    )
    result = await self.db.execute(query)
    pending_chunks = result.scalars().all()
    
    print(f"Found {len(pending_chunks)} pending chunks")
    
    # 2. Process each document's chunks
    for doc_id, chunks in chunks_by_document.items():
        chunk_ids = [chunk.id for chunk in chunks]
        
        # 3. Call the embedding service
        result = await self.embedding_service.generate_batch_embeddings(
            chunk_ids=chunk_ids,
            overwrite=False
        )
        
        print(f"Processed: {result['processed_chunks']}")
```

**What happens here?**
1. Script finds all chunks that don't have embeddings yet
2. Groups them by document
3. Calls `embedding_service.generate_batch_embeddings()` ← **Next step!**

---

## Step 2: Follow to Embedding Service

**File**: `app/services/arabic_legal_embedding_service.py`

**Start at line 339** - This is where embeddings are generated:

```python
# Line 339-431
async def generate_batch_embeddings(
    self,
    chunk_ids: List[int],
    overwrite: bool = False
):
    """Generate embeddings for multiple chunks"""
    
    # 1. Get chunks from database
    query = select(KnowledgeChunk).where(
        KnowledgeChunk.id.in_(chunk_ids)
    )
    result = await self.db.execute(query)
    chunks = result.scalars().all()
    
    # 2. Process in batches (64 at a time)
    for i in range(0, len(chunks), self.batch_size):
        batch = chunks[i:i + self.batch_size]
        
        # 3. Extract text from chunks
        texts = [chunk.content for chunk in batch]
        
        # 4. Generate embeddings for batch
        embeddings = self._encode_batch(texts)  ← **Next step!**
        
        # 5. Save to database
        for chunk, embedding in zip(batch, embeddings):
            chunk.embedding_vector = json.dumps(embedding.tolist())
        
        await self.db.commit()
```

**What happens here?**
1. Gets chunks from database
2. Processes 64 chunks at a time (batch processing)
3. Calls `_encode_batch()` to convert text to numbers ← **Next step!**
4. Saves results to database

---

## Step 3: See How Text Becomes Numbers

**File**: `app/services/arabic_legal_embedding_service.py`

**Start at line 235** - This is where AI magic happens:

```python
# Line 235-264
def _encode_batch(self, texts: List[str]) -> List[np.ndarray]:
    """Encode multiple texts at once"""
    
    # 1. Make sure AI model is loaded
    self._ensure_model_loaded()
    
    # 2. Use AI model to encode all texts
    embeddings = self.sentence_transformer.encode(
        texts,                      # Input: List of text strings
        batch_size=len(texts),      # Process all at once
        convert_to_numpy=True,      # Output: numpy arrays
        show_progress_bar=False
    )
    # Output: List of [768 numbers] for each text
    
    return embeddings
```

**What happens here?**
1. Ensures AI model is loaded (line 151)
2. Feeds all texts to AI model at once
3. AI model returns 768 numbers for each text

---

## Step 4: Understand the AI Model

**File**: `app/services/arabic_legal_embedding_service.py`

**Start at line 151** - Model initialization:

```python
# Line 151-195
def initialize_model(self):
    """Load the AI model"""
    
    # 1. Get model name
    model_path = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    
    # 2. Load the model
    self.sentence_transformer = SentenceTransformer(
        model_path,
        device=self.device  # GPU or CPU
    )
    
    # 3. Get embedding dimension
    test_embedding = self.sentence_transformer.encode("test")
    self.embedding_dimension = len(test_embedding)  # Should be 768
    
    print(f"✅ Model loaded successfully")
    print(f"   Embedding dimension: {self.embedding_dimension}")
```

**What happens here?**
1. Downloads model from Hugging Face (first time only)
2. Loads 278M parameter BERT model
3. Verifies it outputs 768 dimensions

---

## 🔄 Complete Flow Diagram

```
┌────────────────────────────────────────────────────┐
│         YOU RUN THE SCRIPT                         │
│  python scripts/generate_embeddings_batch.py       │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  STEP 1: Find Chunks Without Embeddings            │
│  File: scripts/generate_embeddings_batch.py        │
│  Line: 170-247                                     │
│                                                    │
│  SELECT * FROM knowledge_chunk                     │
│  WHERE embedding_vector IS NULL                    │
│                                                    │
│  Result: 100 chunks found                          │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  STEP 2: Call Embedding Service                    │
│  File: app/services/arabic_legal_embedding_service│
│  Line: 339-431                                     │
│                                                    │
│  await embedding_service.generate_batch_embeddings(│
│      chunk_ids=[1, 2, 3, ..., 100]                │
│  )                                                 │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  STEP 3: Load AI Model (if not loaded)            │
│  File: app/services/arabic_legal_embedding_service│
│  Line: 151-195                                     │
│                                                    │
│  Loading: paraphrase-multilingual-mpnet-base-v2    │
│  Size: 278M parameters                             │
│  Device: GPU (if available) or CPU                 │
│  Output dimension: 768                             │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  STEP 4: Process in Batches                        │
│  File: app/services/arabic_legal_embedding_service│
│  Line: 388-408                                     │
│                                                    │
│  Batch 1: Chunks 1-64                              │
│  Batch 2: Chunks 65-100                            │
│                                                    │
│  For each batch:                                   │
│    texts = [chunk.content for chunk in batch]     │
│    embeddings = model.encode(texts)  ← AI HERE    │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  STEP 5: AI Model Processing                       │
│  (Inside SentenceTransformer.encode())             │
│                                                    │
│  Input: "المادة الأولى: يسمى هذا النظام..."       │
│     ↓                                              │
│  Tokenize: [101, 1234, 5678, ..., 102]           │
│     ↓                                              │
│  BERT Encoding (12 layers)                        │
│     ↓                                              │
│  Mean Pooling                                      │
│     ↓                                              │
│  Output: [0.123, -0.456, ..., 0.234]              │
│          └───────────────────────┘                 │
│                768 numbers                         │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  STEP 6: Save to Database                          │
│  File: app/services/arabic_legal_embedding_service│
│  Line: 399-408                                     │
│                                                    │
│  for chunk, embedding in zip(batch, embeddings):   │
│      chunk.embedding_vector = json.dumps(          │
│          embedding.tolist()                        │
│      )                                             │
│                                                    │
│  await db.commit()                                 │
│                                                    │
│  UPDATE knowledge_chunk                            │
│  SET embedding_vector = '[0.123, -0.456, ...]'    │
│  WHERE id IN (1, 2, 3, ...)                       │
└────────────────┬───────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────┐
│  STEP 7: Print Report                              │
│  File: scripts/generate_embeddings_batch.py        │
│  Line: 312-336                                     │
│                                                    │
│  ✅ PROCESSING COMPLETE!                           │
│  Total Chunks: 100                                 │
│  Processed: 100                                    │
│  Failed: 0                                         │
│  Time: 11.5 seconds                                │
│  Speed: 8.7 chunks/sec                             │
└────────────────────────────────────────────────────┘
```

---

## 📖 Reading Order Summary

**Read these files in this exact order:**

1. **`scripts/generate_embeddings_batch.py`**
   - Lines 170-247: `process_pending_chunks()`
   - Understand: How chunks are found and batched

2. **`app/services/arabic_legal_embedding_service.py`**
   - Lines 339-431: `generate_batch_embeddings()`
   - Understand: How batches are processed

3. **`app/services/arabic_legal_embedding_service.py`**
   - Lines 235-264: `_encode_batch()`
   - Understand: How text becomes numbers

4. **`app/services/arabic_legal_embedding_service.py`**
   - Lines 151-195: `initialize_model()`
   - Understand: How AI model is loaded

---

## 🎓 Key Concepts

### 1. Batch Processing
```python
# Instead of processing one by one (slow):
for chunk in chunks:
    embedding = model.encode(chunk.content)  # 100ms per chunk

# We process many at once (fast):
texts = [chunk.content for chunk in chunks]
embeddings = model.encode(texts)  # 100ms for 64 chunks!
```

### 2. Embedding Storage
```python
# AI model returns numpy array:
embedding = model.encode("text")  # numpy array: [0.123, -0.456, ...]

# We convert to JSON string for database:
embedding_json = json.dumps(embedding.tolist())  # JSON: "[0.123, -0.456, ...]"

# Store in SQLite:
chunk.embedding_vector = embedding_json  # TEXT column
```

### 3. The AI Model
```
Input:  Text (any length, any language)
Model:  paraphrase-multilingual-mpnet-base-v2
Output: 768 floating point numbers
Time:   50-100ms per text (CPU), 10-20ms (GPU)
```

---

## 💡 Simple Test

Want to see it work? Try this:

```bash
# 1. Check what needs embeddings
python scripts/generate_embeddings_batch.py --status

# 2. Generate embeddings
python scripts/generate_embeddings_batch.py --pending

# 3. Watch the output:
# 🚀 Starting PENDING chunks embedding generation
# 📦 Found 50 pending chunks
# 🤖 Initializing model...
# ✅ Model loaded successfully
# ⚙️  Processing batch 1/1
# ✅ Batch processing complete: 50 successful, 0 failed
```

---

## ✅ Now You Know!

**The entire process**:
1. Script finds chunks without embeddings
2. Service loads AI model (if needed)
3. Texts are fed to AI model in batches
4. AI model returns 768 numbers per text
5. Numbers are saved as JSON in database
6. Chunks are now searchable!

**Only 2 files to read**:
- `scripts/generate_embeddings_batch.py` (line 170)
- `app/services/arabic_legal_embedding_service.py` (lines 151, 235, 339)

**That's it!** 🎉

---

**Created**: October 9, 2025  
**Purpose**: Simple code navigation guide  
**Total Files to Read**: 2  
**Total Lines to Read**: ~150 lines

