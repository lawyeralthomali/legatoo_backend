# 🚀 Embedding Generation - Quick Reference

**Last Updated**: October 9, 2025

---

## 🎯 Quick Commands

### Generate Embeddings for All Pending Chunks
```bash
python scripts/generate_embeddings_batch.py --pending
```

### Check System Status
```bash
python scripts/generate_embeddings_batch.py --status
```

### Process Specific Document
```bash
python scripts/generate_embeddings_batch.py --document-id 5
```

### Regenerate All Embeddings
```bash
python scripts/regenerate_embeddings.py
```

---

## 📊 Current Setup

| Setting | Value |
|---------|-------|
| **Model** | `paraphrase-multilingual-mpnet-base-v2` |
| **Dimension** | 768 floats |
| **Batch Size** | 64 chunks |
| **Device** | GPU (if available), else CPU |
| **Speed** | 8-12 chunks/sec (CPU), 40-60 (GPU) |

---

## 🔄 Complete Flow

```
1. Upload Law PDF
      ↓
2. Parse & Extract
      ↓
3. Create Chunks (embedding_vector = NULL)
      ↓
4. Run: python scripts/generate_embeddings_batch.py --pending
      ↓
5. AI Model Loads (768-dim BERT)
      ↓
6. Process Batches (64 chunks at a time)
      ↓
7. Text → [768 numbers] via AI
      ↓
8. Save to Database
      ↓
9. ✅ Ready for Semantic Search!
```

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `scripts/generate_embeddings_batch.py` | Main batch generator |
| `scripts/regenerate_embeddings.py` | Regenerate embeddings |
| `app/services/arabic_legal_embedding_service.py` | Service layer |
| `app/routes/embedding_router.py` | API endpoints |

---

## 🌐 API Endpoints

### Generate for Document
```http
POST /api/v1/embeddings/documents/{id}/generate
Authorization: Bearer <token>
```

### Check Status
```http
GET /api/v1/embeddings/documents/{id}/status
Authorization: Bearer <token>
```

### Batch Generate
```http
POST /api/v1/embeddings/chunks/batch-generate?chunk_ids=1,2,3
Authorization: Bearer <token>
```

---

## 🤖 Supported Models

| Model | Dimension | Speed | Quality |
|-------|-----------|-------|---------|
| **paraphrase-multilingual** (default) | 768 | Fast | Excellent |
| **arabert** | 768 | Fast | Best for Arabic |
| **labse** | 768 | Fast | Very Good |
| **OpenAI text-embedding-3** | 3072 | Slow | Excellent (paid) |

---

## 💡 What Are Embeddings?

```
Text: "فسخ عقد العمل"
  ↓ AI Model
Embedding: [0.123, -0.456, 0.789, ..., 0.234]
           └────────────────────────────────┘
                  768 numbers

Similar meanings = Similar numbers!
```

---

## 📈 Performance

| Chunks | CPU Time | GPU Time |
|--------|----------|----------|
| 100 | ~10 sec | ~2 sec |
| 500 | ~50 sec | ~10 sec |
| 1000 | ~90 sec | ~20 sec |

---

## ✅ Checklist

After uploading a new law:

- [ ] Check status: `python scripts/generate_embeddings_batch.py --status`
- [ ] Generate embeddings: `python scripts/generate_embeddings_batch.py --pending`
- [ ] Verify: Check if `chunks_with_embeddings` increased
- [ ] Test search: Try searching for related terms

---

## 🔍 Troubleshooting

### No embeddings generated?
```bash
# Check if chunks exist
SELECT COUNT(*) FROM knowledge_chunk WHERE law_source_id = 5;

# Check if embeddings exist
SELECT COUNT(*) FROM knowledge_chunk 
WHERE law_source_id = 5 AND embedding_vector IS NOT NULL;

# Run generator
python scripts/generate_embeddings_batch.py --document-id 5
```

### Model not loading?
```bash
# Check dependencies
pip install sentence-transformers torch

# Test model
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2'); print('OK')"
```

### Slow processing?
```bash
# Use GPU if available
python -c "import torch; print(torch.cuda.is_available())"

# Increase batch size (if you have enough RAM)
python scripts/generate_embeddings_batch.py --pending --batch-size 128
```

---

## 📚 Full Documentation

For complete details, see:
- [EMBEDDING_GENERATION_COMPLETE_GUIDE.md](EMBEDDING_GENERATION_COMPLETE_GUIDE.md)

---

**Quick Reference Version 1.0** | October 9, 2025

