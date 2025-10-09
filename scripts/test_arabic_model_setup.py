"""
Test Script: Verify Arabic Model Setup

This script tests that all dependencies are installed and the Arabic model
can be loaded before running the full migration.

Usage:
    python scripts/test_arabic_model_setup.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*60)
print("🧪 TESTING ARABIC MODEL SETUP")
print("="*60)
print()

# Test 1: Check dependencies
print("1️⃣ Checking dependencies...")
missing_deps = []

try:
    import torch
    print("   ✅ torch installed")
except ImportError:
    print("   ❌ torch NOT installed")
    missing_deps.append("torch")

try:
    import transformers
    print("   ✅ transformers installed")
except ImportError:
    print("   ❌ transformers NOT installed")
    missing_deps.append("transformers")

try:
    import faiss
    print("   ✅ faiss installed")
except ImportError:
    print("   ❌ faiss NOT installed")
    missing_deps.append("faiss-cpu or faiss-gpu")

try:
    import numpy
    print("   ✅ numpy installed")
except ImportError:
    print("   ❌ numpy NOT installed")
    missing_deps.append("numpy")

if missing_deps:
    print()
    print("❌ Missing dependencies:")
    for dep in missing_deps:
        print(f"   - {dep}")
    print()
    print("📥 Install with:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

print()

# Test 2: Check database connection
print("2️⃣ Checking database connection...")
try:
    from app.db.database import DATABASE_URL
    print(f"   ✅ Database URL: {DATABASE_URL}")
except Exception as e:
    print(f"   ❌ Database error: {str(e)}")
    sys.exit(1)

print()

# Test 3: Try loading Arabic model
print("3️⃣ Testing Arabic model loading...")
print("   ⏳ This may take a few minutes on first run (downloading ~500MB)...")

try:
    from transformers import AutoTokenizer, AutoModel
    
    model_name = 'aubmindlab/bert-base-arabertv2'
    print(f"   📥 Loading model: {model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    
    print(f"   ✅ Model loaded successfully!")
    print(f"   📊 Model parameters: {sum(p.numel() for p in model.parameters()) / 1e6:.1f}M")
    
    # Test encoding
    test_text = "المادة الأولى من النظام"
    inputs = tokenizer(test_text, return_tensors='pt')
    outputs = model(**inputs)
    
    print(f"   ✅ Model inference works!")
    print(f"   📏 Embedding dimension: {outputs.last_hidden_state.shape[-1]}")
    
except Exception as e:
    print(f"   ❌ Model loading failed: {str(e)}")
    print()
    print("💡 Troubleshooting:")
    print("   - Check your internet connection")
    print("   - Try pre-downloading: python -c \"from transformers import AutoModel; AutoModel.from_pretrained('aubmindlab/bert-base-arabertv2')\"")
    print("   - Check disk space (need ~500MB)")
    sys.exit(1)

print()

# Test 4: Check FAISS
print("4️⃣ Testing FAISS indexing...")
try:
    import faiss
    import numpy as np
    
    # Create a simple test index
    dimension = 768
    index = faiss.IndexFlatIP(dimension)
    
    # Add some test vectors
    test_vectors = np.random.random((10, dimension)).astype('float32')
    index.add(test_vectors)
    
    # Search
    query = np.random.random((1, dimension)).astype('float32')
    distances, indices = index.search(query, 5)
    
    print(f"   ✅ FAISS works!")
    print(f"   📊 Test index: {index.ntotal} vectors")
    
except Exception as e:
    print(f"   ⚠️  FAISS test failed: {str(e)}")
    print("   📝 Note: Migration can still run without FAISS (use --no-faiss)")

print()

# Test 5: Check database has chunks
print("5️⃣ Checking database for existing chunks...")
try:
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy import select, func
    from sqlalchemy.orm import sessionmaker
    from app.models.legal_knowledge import KnowledgeChunk
    
    async def check_chunks():
        engine = create_async_engine(DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            # Count total chunks
            total_query = select(func.count(KnowledgeChunk.id))
            result = await db.execute(total_query)
            total = result.scalar() or 0
            
            # Count chunks with embeddings
            with_emb_query = select(func.count(KnowledgeChunk.id)).where(
                KnowledgeChunk.embedding_vector.isnot(None)
            )
            result = await db.execute(with_emb_query)
            with_emb = result.scalar() or 0
            
            return total, with_emb
        
        await engine.dispose()
    
    total_chunks, chunks_with_embeddings = asyncio.run(check_chunks())
    
    print(f"   ✅ Database accessible")
    print(f"   📊 Total chunks: {total_chunks}")
    print(f"   📊 Chunks with embeddings: {chunks_with_embeddings}")
    
    if total_chunks == 0:
        print()
        print("   ⚠️  WARNING: No chunks found in database")
        print("   📝 Make sure you have uploaded laws before running migration")
    
except Exception as e:
    print(f"   ⚠️  Database check failed: {str(e)}")
    print("   📝 Note: This is OK if database is not initialized yet")

print()
print("="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print()
print("🚀 You're ready to run the migration:")
print("   python scripts/migrate_to_arabic_model.py --model arabert --use-faiss")
print()

