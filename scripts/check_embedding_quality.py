"""
Check embedding quality for stamp forgery chunks
"""
import sys
import asyncio
import json
from sqlalchemy import select, text

sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeChunk


async def check_embeddings():
    """Check embeddings for chunks 6 and 7 (stamp forgery)"""
    
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("🔍 Checking Embedding Quality for Stamp Forgery Chunks")
        print("=" * 80)
        
        # Get chunks 6 and 7
        result = await db.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.id.in_([6, 7, 673, 668, 658]))  # Include some wrong results too
        )
        chunks = result.scalars().all()
        
        for chunk in chunks:
            print(f"\n{'='*80}")
            print(f"📄 Chunk ID: {chunk.id}")
            print(f"   Article ID: {chunk.article_id}")
            print(f"   Content: {chunk.content[:200]}...")
            print(f"   Tokens: {chunk.tokens_count}")
            
            if chunk.embedding_vector:
                embedding = json.loads(chunk.embedding_vector)
                print(f"   ✅ Has embedding: {len(embedding)} dimensions")
                print(f"   Sample values: {embedding[:5]}")
                print(f"   Mean: {sum(embedding)/len(embedding):.4f}")
                print(f"   All zeros? {all(v == 0 for v in embedding)}")
            else:
                print(f"   ❌ NO EMBEDDING!")
        
        # Test search directly with embeddings
        print("\n" + "=" * 80)
        print("🔍 Testing Direct Similarity Search")
        print("=" * 80)
        
        # Get embedding for the query
        from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService
        
        embed_service = ArabicLegalEmbeddingService(db, model_name='arabert', use_faiss=False)
        embed_service.initialize_model()
        
        query = "عقوبة تزوير الطوابع"
        print(f"\n🔎 Query: {query}")
        
        query_embedding = embed_service.encode_text(query)
        print(f"   Query embedding: {len(query_embedding)} dimensions")
        print(f"   Sample: {query_embedding[:5]}")
        
        # Calculate similarity with chunks 6 and 7
        for chunk in chunks:
            if chunk.embedding_vector:
                chunk_embedding = json.loads(chunk.embedding_vector)
                
                # Cosine similarity
                import numpy as np
                query_np = np.array(query_embedding)
                chunk_np = np.array(chunk_embedding)
                
                similarity = np.dot(query_np, chunk_np) / (np.linalg.norm(query_np) * np.linalg.norm(chunk_np))
                
                print(f"\n   📊 Chunk {chunk.id}: Similarity = {similarity:.4f}")
                print(f"      Content: {chunk.content[:100]}...")


if __name__ == "__main__":
    asyncio.run(check_embeddings())

