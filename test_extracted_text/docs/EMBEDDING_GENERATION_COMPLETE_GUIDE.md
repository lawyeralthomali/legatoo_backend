# 🤖 Complete Guide: How Embeddings Are Generated

**Created**: October 9, 2025  
**Purpose**: Complete explanation of embedding generation process, scripts, models, and code

---

## 📋 Table of Contents

1. [What Are Embeddings?](#what-are-embeddings)
2. [Which Scripts Generate Embeddings?](#which-scripts-generate-embeddings)
3. [What Models Are Used?](#what-models-are-used)
4. [How Embeddings Are Generated](#how-embeddings-are-generated)
5. [Code Walkthrough](#code-walkthrough)
6. [API Endpoints](#api-endpoints)
7. [Usage Examples](#usage-examples)

---

## 🎯 What Are Embeddings?

Embeddings are **numerical representations** of text that capture semantic meaning.

### Simple Explanation:
```
Text: "فسخ عقد العمل" (termination of employment contract)
  ↓ AI Model Converts
Embedding: [0.123, -0.456, 0.789, ..., 0.234]
           └────────────────────────────────┘
                  768 numbers

These numbers capture the MEANING of the text!
Similar meanings = Similar numbers
```

### Why Do We Need Them?

1. **Semantic Search**: Find documents by meaning, not just keywords
2. **Fast Comparison**: Compare documents in milliseconds
3. **AI Understanding**: Enable AI to "understand" text content

---

## 🛠️ Which Scripts Generate Embeddings?

### Main Scripts:

| Script | Purpose | Usage |
|--------|---------|-------|
| **`scripts/generate_embeddings_batch.py`** | Generate embeddings for all documents | Main production script |
| **`scripts/regenerate_embeddings.py`** | Regenerate embeddings with new model | Update existing embeddings |
| **API Endpoint** | Generate embeddings via API | Runtime generation |

### 1. Main Batch Generator Script

**File**: `scripts/generate_embeddings_batch.py`

**Purpose**: Process all documents and generate embeddings in batch

**Usage**:
```bash
# Process all documents
python scripts/generate_embeddings_batch.py --all

# Process only chunks without embeddings (recommended)
python scripts/generate_embeddings_batch.py --pending

# Process specific document
python scripts/generate_embeddings_batch.py --document-id 5

# Check system status
python scripts/generate_embeddings_batch.py --status

# Use specific model
python scripts/generate_embeddings_batch.py --pending --model large

# Custom batch size
python scripts/generate_embeddings_batch.py --pending --batch-size 64
```

**What It Does**:
```
1. Connects to database
2. Finds chunks without embeddings
3. Initializes AI model
4. Processes chunks in batches (32-64 at a time)
5. Generates embeddings using AI
6. Saves embeddings to database
7. Reports statistics
```

---

### 2. Regenerate Embeddings Script

**File**: `scripts/regenerate_embeddings.py`

**Purpose**: Regenerate all embeddings with updated model or updated content

**Usage**:
```bash
python scripts/regenerate_embeddings.py
```

**What It Does**:
```
1. Finds all chunks without embeddings
2. Initializes Arabic BERT model
3. Generates embeddings in batches
4. Verifies specific chunks
5. Tests search functionality
```

**When to Use**:
- After updating chunk content
- After switching to new AI model
- After fixing data issues

---

## 🤖 What Models Are Used?

### Current Production Model:

**Model Name**: `paraphrase-multilingual-mpnet-base-v2`

**Details**:
- **Type**: Sentence Transformer (BERT-based)
- **Provider**: Hugging Face
- **Size**: 278M parameters
- **Embedding Dimension**: 768 floats
- **Languages**: 50+ including Arabic
- **Speed**: 50-100ms per text (CPU), 10-20ms (GPU)
- **Max Sequence**: 512 tokens (~2048 characters)

### Alternative Models Supported:

#### 1. **Arabic BERT** (`arabert`)
```python
model_name = 'arabert'
# Specialized for Arabic text
# Better for Arabic legal documents
```

#### 2. **LaBSE** (`labse`)
```python
model_name = 'labse'
# Language-agnostic BERT
# Good for multilingual content
```

#### 3. **OpenAI** (Optional)
```python
# Uses OpenAI API
model = 'text-embedding-3-large'
dimension = 3072
# Higher quality but costs money
```

### Model Comparison:

| Model | Dimension | Speed | Arabic Quality | Cost |
|-------|-----------|-------|----------------|------|
| **paraphrase-multilingual** | 768 | Fast | Good | Free ✅ |
| **arabert** | 768 | Fast | Excellent | Free ✅ |
| **labse** | 768 | Fast | Very Good | Free ✅ |
| **OpenAI text-embedding-3** | 3072 | Slow | Excellent | Paid 💰 |

---

## 🔄 How Embeddings Are Generated

### Complete Workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMBEDDING GENERATION FLOW                     │
└─────────────────────────────────────────────────────────────────┘

STEP 1: Document Upload
┌──────────────────────┐
│ User uploads PDF     │
│ "نظام العمل.pdf"     │
└──────────┬───────────┘
           │
           ▼
STEP 2: Parse & Extract
┌──────────────────────────────────┐
│ PDF → Extract text                │
│ Split into chunks                 │
│ Create KnowledgeChunk records     │
│                                   │
│ Chunk 1: "المادة الأولى..."      │
│ Chunk 2: "المادة الثانية..."     │
│ ...                               │
└──────────┬────────────────────────┘
           │
           │ embedding_vector = NULL (initially)
           │
           ▼
STEP 3: Run Embedding Generation Script
┌──────────────────────────────────────────────────────────┐
│ python scripts/generate_embeddings_batch.py --pending    │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
STEP 4: Find Chunks Without Embeddings
┌──────────────────────────────────────┐
│ SELECT * FROM knowledge_chunk        │
│ WHERE embedding_vector IS NULL       │
│                                      │
│ Result: 600 chunks found             │
└──────────┬───────────────────────────┘
           │
           ▼
STEP 5: Initialize AI Model
┌──────────────────────────────────────────────────┐
│ Load paraphrase-multilingual-mpnet-base-v2      │
│ Model size: 278M parameters                      │
│ Device: GPU (if available) or CPU               │
│ Embedding dimension: 768                         │
└──────────┬───────────────────────────────────────┘
           │
           ▼
STEP 6: Process in Batches
┌─────────────────────────────────────────────────────────┐
│ Batch 1: Chunks 1-32                                     │
│   ├─ Text 1: "المادة الأولى: يسمى هذا النظام..."        │
│   ├─ Text 2: "المادة الثانية: يقصد بالألفاظ..."        │
│   └─ ... (30 more)                                       │
│                                                          │
│   ↓ Feed to AI Model                                    │
│                                                          │
│   AI Model Processing:                                   │
│   ┌────────────────────────────────────────┐            │
│   │ 1. Tokenization                        │            │
│   │    "المادة" → [token_ids]              │            │
│   │                                         │            │
│   │ 2. BERT Encoding (12 layers)           │            │
│   │    [token_ids] → hidden states         │            │
│   │                                         │            │
│   │ 3. Mean Pooling                        │            │
│   │    Average across tokens               │            │
│   │                                         │            │
│   │ 4. Output: [768 floats]                │            │
│   │    [0.123, -0.456, ..., 0.234]         │            │
│   └────────────────────────────────────────┘            │
│                                                          │
│   ↓ Save to Database                                    │
│                                                          │
│ UPDATE knowledge_chunk                                   │
│ SET embedding_vector = '[0.123, -0.456, ..., 0.234]'    │
│ WHERE id IN (1, 2, 3, ..., 32)                          │
│                                                          │
│ ✅ Batch 1 Complete (32 chunks)                         │
└─────────────┬───────────────────────────────────────────┘
              │
              │ Repeat for all batches
              │
              ▼
┌─────────────────────────────────────┐
│ Batch 2: Chunks 33-64   ✅          │
│ Batch 3: Chunks 65-96   ✅          │
│ ...                                  │
│ Batch 19: Chunks 577-600 ✅         │
└─────────────┬───────────────────────┘
              │
              ▼
STEP 7: Final Report
┌──────────────────────────────────────┐
│ ✅ PROCESSING COMPLETE                │
│                                      │
│ Total Chunks: 600                    │
│ Processed: 595                       │
│ Failed: 5                            │
│ Success Rate: 99.2%                  │
│ Time: 45.3 seconds                   │
│ Speed: 13.1 chunks/sec               │
└──────────────────────────────────────┘
```

---

## 💻 Code Walkthrough

### Service Layer: `ArabicLegalEmbeddingService`

**File**: `app/services/arabic_legal_embedding_service.py`

#### 1. Initialize the Service

```python
class ArabicLegalEmbeddingService:
    """Arabic Legal Embedding Service"""
    
    def __init__(
        self, 
        db: AsyncSession, 
        model_name: str = 'paraphrase-multilingual',
        use_faiss: bool = True
    ):
        self.db = db
        self.model_name = model_name
        self.use_faiss = use_faiss
        
        # Model components
        self.sentence_transformer = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Performance settings
        self.batch_size = 64  # Process 64 chunks at once
        self.max_seq_length = 512  # Max tokens per text
        
        # Cache for speed
        self._embedding_cache = {}
```

#### 2. Load the AI Model

```python
def initialize_model(self) -> None:
    """Load the AI model"""
    model_path = self.MODELS.get(self.model_name)
    # e.g., 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
    
    logger.info(f"📥 Loading model: {model_path}")
    logger.info(f"📱 Device: {self.device}")
    
    # Load SentenceTransformer
    self.sentence_transformer = SentenceTransformer(model_path, device=self.device)
    
    # Get embedding dimension
    test_embedding = self.sentence_transformer.encode("test")
    self.embedding_dimension = len(test_embedding)  # 768
    
    logger.info(f"✅ Model loaded successfully")
    logger.info(f"   Embedding dimension: {self.embedding_dimension}")
```

#### 3. Encode Text to Embedding

```python
def encode_text(self, text: str) -> np.ndarray:
    """Convert text to embedding vector"""
    
    # 1. Check cache first
    if text in self._embedding_cache:
        return self._embedding_cache[text]
    
    # 2. Ensure model is loaded
    self._ensure_model_loaded()
    
    # 3. Truncate if too long
    text = self._truncate_text(text, max_tokens=512)
    
    # 4. Use AI model to encode
    embedding = self.sentence_transformer.encode(
        text, 
        convert_to_numpy=True,
        show_progress_bar=False
    )
    # Output: numpy array of 768 floats
    
    # 5. Cache and return
    self._embedding_cache[text] = embedding
    return embedding
```

#### 4. Generate Batch Embeddings

```python
async def generate_batch_embeddings(
    self,
    chunk_ids: List[int],
    overwrite: bool = False
) -> Dict[str, Any]:
    """Generate embeddings for multiple chunks (optimized)"""
    
    # 1. Get chunks from database
    query = select(KnowledgeChunk).where(
        KnowledgeChunk.id.in_(chunk_ids)
    )
    
    if not overwrite:
        # Only chunks without embeddings
        query = query.where(
            KnowledgeChunk.embedding_vector.is_(None)
        )
    
    result = await self.db.execute(query)
    chunks = result.scalars().all()
    
    logger.info(f"📊 Found {len(chunks)} chunks to process")
    
    # 2. Process in batches (64 at a time)
    processed = 0
    failed = 0
    
    for i in range(0, len(chunks), self.batch_size):
        batch = chunks[i:i + self.batch_size]
        logger.info(f"⚙️  Processing batch {i // self.batch_size + 1}")
        
        # 3. Extract texts from chunks
        texts = [chunk.content for chunk in batch]
        
        # 4. Generate embeddings for entire batch
        embeddings = self._encode_batch(texts)
        # Uses AI model.encode() which is optimized for batches
        
        # 5. Save to database
        for chunk, embedding in zip(batch, embeddings):
            try:
                # Convert numpy array to JSON string
                chunk.embedding_vector = json.dumps(embedding.tolist())
                processed += 1
            except Exception as e:
                logger.error(f"❌ Failed chunk {chunk.id}: {str(e)}")
                failed += 1
        
        # 6. Commit batch to database
        await self.db.commit()
    
    # 7. Return statistics
    return {
        "success": True,
        "total_chunks": len(chunks),
        "processed_chunks": processed,
        "failed_chunks": failed,
        "model": self.model_name
    }
```

#### 5. Batch Encoding (Core AI Processing)

```python
def _encode_batch(self, texts: List[str]) -> List[np.ndarray]:
    """Encode multiple texts at once (faster than one-by-one)"""
    
    self._ensure_model_loaded()
    
    # Use SentenceTransformer's batch encoding
    embeddings = self.sentence_transformer.encode(
        texts,
        batch_size=len(texts),
        convert_to_numpy=True,
        show_progress_bar=False
    )
    
    # Returns: List of numpy arrays, each with 768 floats
    return embeddings
```

---

### What Happens Inside the AI Model?

```
Input Text: "المادة الأولى: يسمى هذا النظام نظام العمل"
              ↓

┌─────────────────────────────────────────────────────────┐
│                  AI MODEL PROCESSING                     │
│  (paraphrase-multilingual-mpnet-base-v2)                │
└─────────────────────────────────────────────────────────┘

STEP 1: Tokenization
├─ Split text into tokens (words/subwords)
├─ Convert to token IDs
├─ Add special tokens [CLS], [SEP]
│
│ "المادة" → token_id: 1234
│ "الأولى" → token_id: 5678
│ ...
│
│ Result: [101, 1234, 5678, ..., 102]
│         └─CLS token      SEP token─┘

STEP 2: BERT Encoding (12 Transformer Layers)
├─ Layer 1: Self-attention + Feed-forward
├─ Layer 2: Self-attention + Feed-forward
├─ ...
├─ Layer 12: Self-attention + Feed-forward
│
│ Each layer:
│   ┌──────────────────────────────────┐
│   │ Multi-Head Self-Attention        │
│   │ (captures relationships between  │
│   │  words in the sentence)          │
│   └──────────────┬───────────────────┘
│                  │
│                  ▼
│   ┌──────────────────────────────────┐
│   │ Feed-Forward Neural Network      │
│   │ (processes the attention output) │
│   └──────────────┬───────────────────┘
│                  │
│                  ▼
│   Hidden States: [batch, seq_len, 768]

STEP 3: Mean Pooling
├─ Average all token embeddings
├─ Reduces [seq_len, 768] → [768]
│
│ Formula: mean(hidden_states, dim=1)
│
│ Result: [0.123, -0.456, 0.789, ..., 0.234]
│         └─────────────────────────────────┘
│                    768 values

STEP 4: Normalization (Optional)
├─ Normalize vector to unit length
├─ Makes cosine similarity more meaningful
│
│ Formula: embedding / ||embedding||
│
│ Final Output: [0.0145, -0.0538, 0.0931, ..., 0.0276]
│               └────────────────────────────────────────┘
│                        768 normalized values
```

---

## 📊 Database Storage

### How Embeddings Are Stored:

```sql
-- Table: knowledge_chunk
CREATE TABLE knowledge_chunk (
    id INTEGER PRIMARY KEY,
    content TEXT,  -- Original text
    embedding_vector TEXT,  -- JSON array of 768 floats
    law_source_id INTEGER,
    ...
);

-- Example Record:
INSERT INTO knowledge_chunk VALUES (
    123,
    'المادة الأولى: يسمى هذا النظام نظام العمل',
    '[0.123, -0.456, 0.789, ..., 0.234]',  -- 768 floats as JSON
    5,
    ...
);
```

### Storage Format:

```python
# In Python
embedding = [0.123, -0.456, 0.789, ...]  # numpy array or list

# Convert to JSON string for SQLite
embedding_json = json.dumps(embedding)
# Result: '[0.123, -0.456, 0.789, ...]'

# Store in database
chunk.embedding_vector = embedding_json

# Later, retrieve from database
embedding_str = chunk.embedding_vector
embedding = json.loads(embedding_str)
# Result: [0.123, -0.456, 0.789, ...]
```

---

## 🌐 API Endpoints

### 1. Generate Embeddings for Document

```http
POST /api/v1/embeddings/documents/{document_id}/generate
Authorization: Bearer <JWT_TOKEN>
```

**Parameters**:
- `document_id`: ID of the document
- `overwrite`: (optional) Regenerate existing embeddings

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/embeddings/documents/5/generate?overwrite=false" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Response**:
```json
{
  "success": true,
  "message": "Generated embeddings for 45 chunks in document 5",
  "data": {
    "document_id": 5,
    "total_chunks": 45,
    "processed_chunks": 45,
    "failed_chunks": 0,
    "processing_time": "15.2s"
  },
  "errors": []
}
```

---

### 2. Generate Embeddings for Specific Chunks

```http
POST /api/v1/embeddings/chunks/batch-generate?chunk_ids=1,2,3,4,5
Authorization: Bearer <JWT_TOKEN>
```

**Parameters**:
- `chunk_ids`: List of chunk IDs (max 1000)
- `overwrite`: (optional) Regenerate existing embeddings

**Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/embeddings/chunks/batch-generate?chunk_ids=1,2,3,4,5&overwrite=false" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

### 3. Check Embedding Status

```http
GET /api/v1/embeddings/documents/{document_id}/status
Authorization: Bearer <JWT_TOKEN>
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/embeddings/documents/5/status" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Response**:
```json
{
  "success": true,
  "message": "Embedding status retrieved",
  "data": {
    "document_id": 5,
    "total_chunks": 45,
    "chunks_with_embeddings": 45,
    "chunks_without_embeddings": 0,
    "completion_percentage": 100.0,
    "status": "complete"
  },
  "errors": []
}
```

---

## 🔧 Usage Examples

### Example 1: Generate Embeddings After Upload

```python
# After uploading a law PDF
import requests

# 1. Upload law
response = requests.post(
    "http://localhost:8000/api/v1/laws/upload",
    files={"pdf_file": open("law.pdf", "rb")},
    data={
        "law_name": "نظام العمل السعودي",
        "law_type": "law"
    },
    headers={"Authorization": f"Bearer {token}"}
)

law_id = response.json()["data"]["law_source"]["id"]

# 2. Generate embeddings
response = requests.post(
    f"http://localhost:8000/api/v1/embeddings/documents/{law_id}/generate",
    headers={"Authorization": f"Bearer {token}"}
)

print(response.json())
# {
#   "success": true,
#   "message": "Generated embeddings for 45 chunks..."
# }
```

---

### Example 2: Batch Generate via Script

```bash
# Check current status
python scripts/generate_embeddings_batch.py --status

# Output:
# 📊 SYSTEM STATUS
# 📦 Total chunks: 600
# ✅ With embeddings: 200
# ⏳ Without embeddings: 400
# 📈 Completion: 33.33%

# Generate embeddings for pending chunks
python scripts/generate_embeddings_batch.py --pending

# Output:
# 🚀 Starting PENDING chunks embedding generation
# 📦 Found 400 pending chunks
# ⚙️  Processing batch 1/13
# ⚙️  Processing batch 2/13
# ...
# ✅ Batch processing complete: 395 successful, 5 failed
# ⏱️  Duration: 45.3 seconds
# ⚡ Speed: 8.7 chunks/sec
```

---

### Example 3: Regenerate with New Model

```bash
# Update to Arabic BERT model
python scripts/regenerate_embeddings.py

# This will:
# 1. Find chunks without embeddings
# 2. Load Arabic BERT model
# 3. Generate embeddings
# 4. Verify results
# 5. Test search functionality
```

---

## 📈 Performance Metrics

### Processing Speed:

| Hardware | Speed (chunks/sec) | Time for 1000 chunks |
|----------|-------------------|---------------------|
| **CPU (Intel i7)** | 8-12 | ~90 seconds |
| **GPU (NVIDIA T4)** | 40-60 | ~20 seconds |
| **GPU (NVIDIA A100)** | 100-150 | ~7 seconds |

### Memory Usage:

| Model | RAM (CPU) | VRAM (GPU) |
|-------|-----------|------------|
| paraphrase-multilingual | ~2GB | ~1.5GB |
| arabert | ~2GB | ~1.5GB |
| OpenAI API | Minimal | N/A |

### Batch Size Impact:

| Batch Size | Speed | Memory |
|------------|-------|--------|
| 16 | Slower | Low |
| 32 | Balanced | Medium |
| 64 | **Optimal** | High |
| 128 | Fastest | Very High |

---

## ✅ Summary

### The Complete Process:

1. **Upload Document** → PDF extracted and chunked
2. **Run Script** → `python scripts/generate_embeddings_batch.py --pending`
3. **Load Model** → AI model initialized (768-dimensional BERT)
4. **Process Batches** → Chunks processed 64 at a time
5. **Generate Embeddings** → Each text → [768 numbers]
6. **Save to DB** → Stored as JSON in `embedding_vector` column
7. **Enable Search** → Now available for semantic search!

### Key Files:

- **Scripts**: `scripts/generate_embeddings_batch.py`, `scripts/regenerate_embeddings.py`
- **Service**: `app/services/arabic_legal_embedding_service.py`
- **API**: `app/routes/embedding_router.py`
- **Models**: Sentence Transformers (BERT-based)

### Default Model:

- **Name**: `paraphrase-multilingual-mpnet-base-v2`
- **Dimension**: 768 floats
- **Speed**: 8-12 chunks/sec (CPU), 40-60 (GPU)
- **Quality**: Excellent for Arabic + English

---

**Created**: October 9, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅

