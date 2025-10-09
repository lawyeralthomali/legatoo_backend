"""Check embedding dimension to verify which model was used."""
import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.legal_knowledge import KnowledgeChunk

async def check_embedding_dimension():
    async with AsyncSessionLocal() as db:
        # Get first chunk with embedding
        chunk = await db.scalar(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.embedding_vector.isnot(None))
            .limit(1)
        )
        
        if not chunk:
            print("❌ No chunks with embeddings found!")
            return
        
        # Parse embedding
        embedding = json.loads(chunk.embedding_vector)
        dimension = len(embedding)
        
        print("="*60)
        print("🔍 EMBEDDING ANALYSIS")
        print("="*60)
        print(f"📊 Embedding Dimension: {dimension}")
        print(f"📝 Sample Chunk ID: {chunk.id}")
        print(f"📄 Content Preview: {chunk.content[:100]}...")
        print("="*60)
        
        if dimension == 768:
            print("✅ CORRECT: Using Arabic BERT (768-dim)")
        elif dimension == 384:
            print("❌ WRONG: Using OLD model (384-dim)")
            print("⚠️  ACTION REQUIRED: Run migrate_to_arabic_model.py")
        else:
            print(f"⚠️  UNKNOWN: Unexpected dimension {dimension}")
        
        print("="*60)
        
        # Check FAISS index
        faiss_path = Path("faiss_indexes/faiss_index.bin")
        faiss_exists = faiss_path.exists()
        print(f"🗂️  FAISS Index: {'✅ EXISTS' if faiss_exists else '❌ MISSING'}")
        
        if not faiss_exists:
            print("⚠️  ACTION REQUIRED: FAISS index missing! Run migrate_to_arabic_model.py")

if __name__ == "__main__":
    asyncio.run(check_embedding_dimension())

