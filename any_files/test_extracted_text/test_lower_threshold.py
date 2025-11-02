"""
Test with lower threshold to diagnose if embeddings are working.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_search_service import ArabicLegalSearchService


async def test_low_threshold():
    """Test search with very low threshold to see all matches."""
    print("=" * 80)
    print("TESTING WITH LOW THRESHOLD (0.3)")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # Create and initialize search service
            print("\n📥 Initializing search service...")
            search_service = ArabicLegalSearchService(db, use_faiss=True)
            await search_service.initialize()
            print("✅ Service ready!")
            
            # Test with low threshold
            query = "حقوق العامل"
            threshold = 0.3  # Very low threshold
            
            print(f"\n🔍 Query: '{query}'")
            print(f"📊 Threshold: {threshold}")
            print("-" * 60)
            
            results = await search_service.find_similar_laws(
                query=query,
                top_k=10,
                threshold=threshold,
                use_fast_search=True
            )
            
            if len(results) > 0:
                print(f"\n✅ Found {len(results)} results:")
                print("\nTop 10 Results:")
                for i, result in enumerate(results, 1):
                    print(f"\n[{i}] Similarity: {result['similarity']:.4f}")
                    print(f"    Chunk ID: {result['chunk_id']}")
                    print(f"    Content: {result['content'][:150]}...")
                    if 'law_metadata' in result:
                        print(f"    Law: {result['law_metadata'].get('law_name', 'N/A')}")
                    if 'article_metadata' in result:
                        article_num = result['article_metadata'].get('article_number', 'N/A')
                        article_title = result['article_metadata'].get('title', 'N/A')
                        print(f"    Article: {article_num} - {article_title}")
            else:
                print(f"\n❌ PROBLEM: No results even with threshold 0.3!")
                print("This suggests an issue with the embeddings or search process.")
            
            # Test another query
            print("\n" + "=" * 80)
            query2 = "العمل"  # Simpler query
            print(f"\n🔍 Query: '{query2}' (simpler)")
            print(f"📊 Threshold: {threshold}")
            print("-" * 60)
            
            results2 = await search_service.find_similar_laws(
                query=query2,
                top_k=10,
                threshold=threshold,
                use_fast_search=True
            )
            
            if len(results2) > 0:
                print(f"\n✅ Found {len(results2)} results:")
                for i, result in enumerate(results2[:5], 1):
                    print(f"\n[{i}] Similarity: {result['similarity']:.4f}")
                    print(f"    Content: {result['content'][:100]}...")
            else:
                print(f"\n❌ Still no results!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_low_threshold())

