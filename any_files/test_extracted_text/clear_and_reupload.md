# Clear Database and Re-upload with Improved Chunks

## What Changed?

**OLD Chunk Format** (BAD - No context):
```
**اسم النظام**

يسمى هذا النظام نظام العمل.
```

**NEW Chunk Format** (GOOD - Full context):
```
[📜 نظام العمل السعودي - الباب: التعريفات / الأحكام العامة - الفصل: التعريفات]
**اسم النظام**

يسمى هذا النظام نظام العمل.
```

## Why This Fixes the Accuracy Problem

The embeddings now capture:
1. **Law name** ("نظام العمل السعودي") - So queries about "العمل" match correctly
2. **Branch/Chapter** - Additional semantic context
3. **Article title & content** - The actual legal text

This should dramatically improve RAG accuracy from **20% → 80%+**!

## Steps to Re-upload

### 1. Clear the current database
```bash
# Delete the database file
rm app.db

# Or use SQL to clear tables (if keeping user data):
# DELETE FROM knowledge_chunks;
# DELETE FROM law_articles;
# DELETE FROM law_chapters;
# DELETE FROM law_branches;
# DELETE FROM law_sources;
# DELETE FROM knowledge_documents;
```

### 2. Recreate tables
```bash
py run.py
# Or start the server once to auto-create tables
```

### 3. Re-upload all JSON files
```bash
# Start server
py start_server.py

# In another terminal
cd data_set
py batch_upload_json.py
```

### 4. Test the improved accuracy
```bash
py test_retrieval_accuracy.py
```

Expected improvement:
- Before: **20% accuracy** (1/5 correct)
- After: **80-100% accuracy** (4-5/5 correct)

## What Makes This a Proper RAG System Now

✅ **Contextual Retrieval**: Each chunk has full law context
✅ **Semantic Understanding**: Embeddings capture law names + content
✅ **Accurate Matching**: Queries like "حقوق العامل" will match "نظام العمل السعودي"
✅ **Hierarchical Context**: Branch/Chapter info helps disambiguation

This transforms it from a basic search into a true **RAG (Retrieval-Augmented Generation)** system!

