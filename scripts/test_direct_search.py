"""Test direct search using ArabicLegalSearchService."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_search_service import ArabicLegalSearchService

async def test_search():
    async with AsyncSessionLocal() as db:
        # Initialize search service
        search_service = ArabicLegalSearchService(db, use_faiss=True)  # uses paraphrase-multilingual by default
        
        query = "عقوبة تزوير الطوابع"
        
        print("="*80)
        print(f"🔍 TESTING SEARCH")
        print("="*80)
        print(f"Query: {query}")
        print(f"Model: paraphrase-multilingual (NEW)")
        print(f"Use FAISS: True")
        print("="*80)
        
        try:
            # Test search
            results = await search_service.find_similar_laws(
                query=query,
                top_k=5,
                threshold=0.5  # Lower threshold
            )
            
            print(f"\n📊 Results found: {len(results)}")
            
            if len(results) == 0:
                print("\n❌ NO RESULTS! Debugging...")
                
                # Try with even lower threshold
                results_low = await search_service.find_similar_laws(
                    query=query,
                    top_k=5,
                    threshold=0.0
                )
                print(f"📊 With threshold=0.0: {len(results_low)} results")
                
                if len(results_low) > 0:
                    print("\n✅ Results found with threshold=0.0!")
                    for i, result in enumerate(results_low[:3], 1):
                        print(f"\n{i}. Chunk {result['chunk_id']}")
                        print(f"   Similarity: {result['similarity']:.4f}")
                        print(f"   Content: {result['content'][:100]}...")
                else:
                    print("\n❌ Still no results even with threshold=0.0")
                    print("🔍 Checking if search service is working...")
                    
            else:
                print("\n✅ RESULTS FOUND!")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. Chunk {result['chunk_id']}")
                    print(f"   Similarity: {result['similarity']:.4f}")
                    print(f"   Law: {result.get('law_metadata', {}).get('law_name', 'Unknown')}")
                    print(f"   Content: {result['content'][:150]}...")
                    
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())

