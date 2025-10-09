"""Test different query variations for stamp forgery."""
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

async def test_variations():
    async with AsyncSessionLocal() as db:
        # Get chunk 6
        chunk_6 = await db.scalar(select(KnowledgeChunk).where(KnowledgeChunk.id == 6))
        
        # Initialize embedding service
        embedding_service = ArabicLegalEmbeddingService(db, model_name='arabert', use_faiss=True)
        embedding_service.initialize_model()
        
        chunk_emb = np.array(json.loads(chunk_6.embedding_vector))
        
        print("="*80)
        print("🧪 TESTING QUERY VARIATIONS FOR CHUNK 6")
        print("="*80)
        print(f"\n📄 Chunk 6 content:")
        print(f"   {chunk_6.content[:150]}...")
        
        queries = [
            "عقوبة تزوير الطوابع",
            "عقوبة تزوير طابع",
            "تزوير طابع",
            "تزوير الطوابع",
            "عقوبة",
            "السجن",
            "النظام الجزائي لجرائم التزوير",
            "من زور طابعا",
            "غرامة",
        ]
        
        print("\n" + "="*80)
        print("📊 SIMILARITY SCORES:")
        print("="*80)
        
        for query in queries:
            query_emb = embedding_service.encode_text(query)
            similarity = embedding_service.cosine_similarity(query_emb, chunk_emb)
            
            status = "✅" if similarity > 0.7 else ("⚠️" if similarity > 0.5 else "❌")
            print(f"{status} '{query}': {similarity:.4f}")

if __name__ == "__main__":
    asyncio.run(test_variations())

