"""
Regenerate embeddings for chunks 6 and 7 (stamp forgery)
"""
import sys
import asyncio

sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService


async def regenerate():
    async with AsyncSessionLocal() as db:
        print("🔄 Regenerating embeddings for chunks 6 and 7...")
        
        # Initialize service
        service = ArabicLegalEmbeddingService(db, model_name='arabert', use_faiss=False)
        service.initialize_model()
        
        # Generate for chunks 6 and 7
        result = await service.generate_batch_embeddings(
            chunk_ids=[6, 7],
            overwrite=True
        )
        
        print(f"\n✅ Result:")
        print(f"   Processed: {result['processed_chunks']}")
        print(f"   Failed: {result['failed_chunks']}")
        print(f"   Time: {result['processing_time']}")
        
        # Test search
        print("\n🔍 Testing search...")
        from app.services.arabic_legal_search_service import ArabicLegalSearchService
        
        search_service = ArabicLegalSearchService(db, model_name='arabert', use_faiss=False)
        search_service.embedding_service.initialize_model()
        
        query = "عقوبة تزوير الطوابع"
        results = await search_service.find_similar_laws(
            query=query,
            top_k=3,
            threshold=0.3
        )
        
        print(f"\n📊 Search results for: {query}")
        print("="*80)
        
        for i, r in enumerate(results, 1):
            print(f"\n{i}. Chunk {r['chunk_id']} - Similarity: {r['similarity']:.4f}")
            print(f"   {r['content'][:150]}...")
            if 'article_metadata' in r:
                print(f"   Article: {r['article_metadata']['title']}")


asyncio.run(regenerate())

