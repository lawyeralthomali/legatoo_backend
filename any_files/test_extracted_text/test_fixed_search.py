"""
Quick test to verify the search fix is working.
Tests the search functionality after adding service initialization.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_search_service import ArabicLegalSearchService


async def test_search_with_initialization():
    """Test search with proper initialization."""
    print("=" * 80)
    print("TESTING FIXED SEARCH FUNCTIONALITY")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # Create search service
            print("\n1️⃣ Creating search service...")
            search_service = ArabicLegalSearchService(db, use_faiss=True)
            
            # Initialize the service (THIS IS THE FIX!)
            print("2️⃣ Initializing search service (loading model + building FAISS index)...")
            await search_service.initialize()
            print("✅ Search service initialized successfully!")
            
            # Test queries
            test_queries = [
                ("حقوق العامل", 0.5),
                ("إنهاء عقد العمل", 0.5),
                ("الإجازات السنوية", 0.5),
                ("رواتب العمال", 0.5),
            ]
            
            print("\n" + "=" * 80)
            print("TESTING SEARCH QUERIES")
            print("=" * 80)
            
            for query, threshold in test_queries:
                print(f"\n🔍 Query: '{query}' (threshold: {threshold})")
                print("-" * 60)
                
                results = await search_service.find_similar_laws(
                    query=query,
                    top_k=5,
                    threshold=threshold,
                    use_fast_search=True
                )
                
                if len(results) > 0:
                    print(f"✅ Found {len(results)} results:")
                    for i, result in enumerate(results[:3], 1):  # Show top 3
                        print(f"\n   [{i}] Similarity: {result['similarity']:.4f}")
                        print(f"       Content: {result['content'][:120]}...")
                        if 'law_metadata' in result:
                            print(f"       Law: {result['law_metadata'].get('law_name', 'N/A')}")
                        if 'article_metadata' in result:
                            print(f"       Article: {result['article_metadata'].get('article_number', 'N/A')}")
                else:
                    print(f"⚠️  No results found (threshold might be too high)")
            
            print("\n" + "=" * 80)
            print("TEST COMPLETE")
            print("=" * 80)
            print("\n✅ If you see search results above, the fix is working!")
            print("❌ If no results, try lowering the threshold or check embeddings.")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_search_with_initialization())

