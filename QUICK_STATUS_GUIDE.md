# 🚀 Quick Status Guide - Two-Step Upload Process

## 📌 TL;DR

**Before:** Upload → Status: `processed` (automatic)  
**Now:** Upload → Status: `raw` → Generate Embeddings → Status: `processed`

## ⚡ Quick Start

### 1️⃣ Upload Your Document
```bash
POST /api/v1/laws/upload
```
**Result:** Status = `raw` (not searchable yet)

### 2️⃣ Generate Embeddings (REQUIRED!)
```bash
POST /api/v1/laws/{document_id}/generate-embeddings
```
**Result:** Status = `processed` (searchable)

### 3️⃣ Query
```bash
POST /api/v1/laws/query
```
**Result:** Get AI-generated answers

## 📊 Status Reference

| Status | SQL Data | Chroma Embeddings | Searchable | Next Action |
|--------|----------|-------------------|------------|-------------|
| `raw` | ✅ Yes | ❌ No | ❌ No | Generate embeddings |
| `processing` | ✅ Yes | 🔄 Generating | ❌ No | Wait |
| `processed` | ✅ Yes | ✅ Yes | ✅ Yes | Ready to query |

## ⚠️ Common Mistakes

### ❌ Mistake #1: Not generating embeddings
```javascript
// Wrong - document not searchable!
uploadDocument(file);
queryDocuments(query); // ❌ Returns "no documents found"
```

### ✅ Correct way:
```javascript
// Right - two-step process
const upload = await uploadDocument(file);
await generateEmbeddings(upload.data.document_id); // Required!
await queryDocuments(query); // ✅ Works!
```

### ❌ Mistake #2: Assuming immediate availability
```javascript
// Wrong - embeddings take time to generate
await generateEmbeddings(docId);
await queryDocuments(query); // ❌ Might fail if still processing
```

### ✅ Correct way:
```javascript
// Right - wait for completion or poll status
await generateEmbeddings(docId);
await sleep(30000); // Wait 30 seconds
// Or poll GET /api/v1/laws/{id} until status === 'processed'
await queryDocuments(query); // ✅ Works!
```

## 🔧 Migration Checklist

- [ ] Update upload flow to call `/generate-embeddings`
- [ ] Check document status before querying
- [ ] Update UI to show status ('raw', 'processing', 'processed')
- [ ] Add "Generate Embeddings" button for raw documents
- [ ] Restart server after code update
- [ ] Re-upload or regenerate embeddings for existing documents

## 💡 Why This Change?

**Problem Before:**
- Upload endpoint was slow (generating embeddings inline)
- Status said "processed" even if embeddings failed
- No way to retry embeddings without re-uploading

**Benefits Now:**
- ⚡ Fast upload (SQL only)
- 🎯 Accurate status tracking
- 🔄 Can retry embeddings separately
- 📊 Clear two-step workflow

## 🆘 Need Help?

See `STATUS_WORKFLOW_UPDATE.md` for detailed documentation.

