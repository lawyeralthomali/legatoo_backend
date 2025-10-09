"""Test chunk 6 directly for stamp forgery."""
import asyncio
import sys
import json
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.legal_knowledge import KnowledgeChunk
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService

async def test_chunk_6():
    async with AsyncSessionLocal() as db:
        # Get chunk 6 (stamp forgery)
        chunk_6 = await db.scalar(select(KnowledgeChunk).where(KnowledgeChunk.id == 6))
        chunk_7 = await db.scalar(select(KnowledgeChunk).where(KnowledgeChunk.id == 7))
        
        print("="*80)
        print("🔍 TESTING CHUNKS 6 & 7 (Stamp Forgery)")
        print("="*80)
        
        # Initialize embedding service
        embedding_service = ArabicLegalEmbeddingService(db, model_name='arabert', use_faiss=True)
        embedding_service.initialize_model()
        
        # Encode query
        query = "عقوبة تزوير الطوابع"
        query_embedding = embedding_service.encode_text(query)
        
        print(f"\n📝 Query: {query}")
        print(f"📊 Query embedding dimension: {len(query_embedding)}")
        
        for chunk in [chunk_6, chunk_7]:
            if chunk:
                print(f"\n" + "="*80)
                print(f"📄 Chunk {chunk.id}:")
                print(f"   Content: {chunk.content[:150]}...")
                print(f"   Has embedding: {chunk.embedding_vector is not None}")
                
                if chunk.embedding_vector:
                    chunk_emb = np.array(json.loads(chunk.embedding_vector))
                    print(f"   Embedding dimension: {len(chunk_emb)}")
                    
                    # Calculate similarity
                    similarity = embedding_service.cosine_similarity(query_embedding, chunk_emb)
                    print(f"   🎯 Similarity: {similarity:.4f}")
                    
                    if similarity < 0.7:
                        print(f"   ❌ LOW SIMILARITY! Expected > 0.85 for exact match")
                    else:
                        print(f"   ✅ Good similarity!")

if __name__ == "__main__":
    asyncio.run(test_chunk_6())

