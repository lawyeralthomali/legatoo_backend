# 🤖 Available AI Models

**Quick Reference for Embedding Models**

---

## ✅ Available Models

| Model Name | Description | Best For |
|------------|-------------|----------|
| **`paraphrase-multilingual`** | Default model (recommended) | Arabic + English, fast, reliable |
| **`arabert-st`** | AraBERT Sentence Transformer | Best for pure Arabic text |
| **`arabic-st`** | Arabic BERT Embedding | Good for Arabic legal documents |
| **`labse`** | Language-agnostic BERT | Multilingual, general purpose |

---

## 🎯 Default Model (Recommended)

**Name**: `paraphrase-multilingual`

**Full Name**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`

**Details**:
- ✅ Supports 50+ languages including Arabic and English
- ✅ 768-dimensional embeddings
- ✅ Fast: 8-12 chunks/second (CPU)
- ✅ Well-tested and reliable
- ✅ **Currently used in production**

**Use in code**:
```python
embedding_service = ArabicLegalEmbeddingService(
    db=db,
    model_name='paraphrase-multilingual',  # ← Default
    use_faiss=True
)
```

---

## 🔧 How to Change Model

### In Scripts:

**File**: `scripts/regenerate_embeddings.py`
```python
# Line 52-56
embedding_service = ArabicLegalEmbeddingService(
    db=db,
    model_name='paraphrase-multilingual',  # ← Change this
    use_faiss=True
)
```

### Available Options:
- `'paraphrase-multilingual'` ← **Default (recommended)**
- `'arabert-st'` ← Best for Arabic
- `'arabic-st'` ← Alternative Arabic model
- `'labse'` ← Multilingual alternative

---

## ⚠️ Error You Fixed

**Before (Wrong)**:
```python
model_name='arabert'  # ❌ This doesn't exist!
```

**After (Correct)**:
```python
model_name='paraphrase-multilingual'  # ✅ This exists!
```

**Valid model names**:
- ✅ `paraphrase-multilingual`
- ✅ `arabert-st` (not `arabert`)
- ✅ `arabic-st`
- ✅ `labse`
- ❌ `arabert` (doesn't exist)

---

## 📊 Model Comparison

| Feature | paraphrase-multilingual | arabert-st | labse |
|---------|------------------------|------------|-------|
| **Languages** | 50+ | Arabic focus | 100+ |
| **Dimension** | 768 | 768 | 768 |
| **Speed** | Fast | Fast | Medium |
| **Arabic Quality** | Very Good | Excellent | Good |
| **English Quality** | Excellent | Poor | Very Good |
| **Recommended** | ✅ Yes | For Arabic-only | Alternative |

---

## 🚀 Quick Test

```bash
# Test with default model
python scripts/regenerate_embeddings.py

# This will use: paraphrase-multilingual ✅
```

---

## 🎯 Summary

**Fixed Error**:
- ❌ `model_name='arabert'` (doesn't exist)
- ✅ `model_name='paraphrase-multilingual'` (correct!)

**Default Model**:
- `paraphrase-multilingual` (768 dimensions)
- Fast, reliable, supports Arabic + English
- Currently used in production ✅

**Other Options**:
- `arabert-st` for pure Arabic text
- `arabic-st` alternative Arabic model
- `labse` for multilingual support

---

**Your script is now fixed!** ✅

Run it again:
```bash
python scripts/regenerate_embeddings.py
```

It should work now! 🎉

