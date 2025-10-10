"""
Regenerate Embeddings for Updated Chunks
=========================================

After updating chunk content to include article titles,
we need to regenerate embeddings using the Arabic model.
"""
import sys
import asyncio
from sqlalchemy import select, func

sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeChunk
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService


async def regenerate_embeddings():
    """Regenerate embeddings for ALL chunks (overwrite existing)"""
    
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("🔄 Regenerating ALL Embeddings (Overwrite Mode)")
        print("=" * 80)
        
        # 1. Count ALL chunks (including those with embeddings)
        result = await db.execute(
            select(func.count(KnowledgeChunk.id))
        )
        total_chunks = result.scalar()
        
        print(f"\n📊 Total chunks in database: {total_chunks}")
        
        if total_chunks == 0:
            print("⚠️  No chunks found in database!")
            return
        
        # 2. Get ALL chunk IDs (will overwrite existing embeddings)
        result = await db.execute(
            select(KnowledgeChunk.id)
            .order_by(KnowledgeChunk.id)
        )
        chunk_ids = [row[0] for row in result.all()]
        
        print(f"🎯 Processing {len(chunk_ids)} chunks...")
        print(f"📝 Sample IDs: {chunk_ids[:10]}...")
        
        # 3. Initialize Arabic embedding service (uses sts-arabert default)
        print(f"\n🤖 Initializing STS-AraBERT model (256-dim)...")
        embedding_service = ArabicLegalEmbeddingService(
            db=db,
            # model_name not specified = uses default 'sts-arabert'
            use_faiss=True
        )
        embedding_service.initialize_model()
        
        # 4. Generate embeddings in batches (OVERWRITE EXISTING)
        print(f"\n⚡ Starting embedding generation (OVERWRITE MODE)...")
        print(f"⚠️  This will regenerate ALL {len(chunk_ids)} embeddings!")
        result = await embedding_service.generate_batch_embeddings(
            chunk_ids=chunk_ids,
            overwrite=True  # ← This forces regeneration!
        )
        
        # 5. Show results
        print(f"\n{'='*80}")
        print(f"✅ EMBEDDING GENERATION COMPLETE!")
        print(f"{'='*80}")
        print(f"📊 Processed: {result['processed_chunks']} chunks")
        print(f"❌ Failed: {result['failed_chunks']} chunks")
        print(f"⏱️  Time: {result['processing_time']}")
        print(f"⚡ Speed: {result['speed']}")
        print(f"🤖 Model: {result['model']}")
        
        # 6. Verify specific chunks
        await verify_stamp_chunks(db)


async def verify_stamp_chunks(db):
    """Verify that stamp forgery chunks now have proper embeddings"""
    
    print(f"\n{'='*80}")
    print(f"🧪 Verifying Stamp Forgery Chunks")
    print(f"{'='*80}")
    
    # Get chunks 6 and 7
    result = await db.execute(
        select(KnowledgeChunk)
        .where(KnowledgeChunk.id.in_([6, 7]))
    )
    chunks = result.scalars().all()
    
    for chunk in chunks:
        has_embedding = chunk.embedding_vector is not None
        status = "✅" if has_embedding else "❌"
        
        print(f"\n{status} Chunk {chunk.id}:")
        print(f"   Content (first 100 chars): {chunk.content[:100]}...")
        print(f"   Has embedding: {has_embedding}")
        
        if has_embedding:
            import json
            embedding = json.loads(chunk.embedding_vector)
            print(f"   Embedding dimension: {len(embedding)}")


async def test_search():
    """Test search with the updated chunks"""
    
    print(f"\n{'='*80}")
    print(f"🔍 Testing Search: عقوبة تزوير الطوابع")
    print(f"{'='*80}")
    
    async with AsyncSessionLocal() as db:
        from app.services.arabic_legal_search_service import ArabicLegalSearchService
        
        # Use default arabert-st model
        search_service = ArabicLegalSearchService(db, use_faiss=False)
        
        # Initialize embedding service
        search_service.embedding_service.initialize_model()
        
        query = "عقوبة تزوير الطوابع"
        results = await search_service.find_similar_laws(
            query=query,
            top_k=5,
            threshold=0.3  # Lower threshold to see all results
        )
        
        print(f"\n📊 Found {len(results)} results:")
        print(f"-" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Chunk {result['chunk_id']} - Similarity: {result['similarity']:.4f}")
            print(f"   Content: {result['content'][:150]}...")
            if 'article_metadata' in result:
                print(f"   Article: {result['article_metadata']['article_number']} - {result['article_metadata']['title']}")


if __name__ == "__main__":
    print("🚀 Starting Embedding Regeneration...")
    asyncio.run(regenerate_embeddings())
    
    print("\n\n" + "="*80)
    print("🔍 NOW TESTING SEARCH...")
    print("="*80)
    asyncio.run(test_search())

