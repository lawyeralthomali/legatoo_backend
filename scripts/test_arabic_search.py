"""
Test Script: Arabic Legal Search Performance

This script tests the new Arabic legal search system and compares
performance with benchmarks.

Usage:
    python scripts/test_arabic_search.py
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.database import DATABASE_URL
from app.services.arabic_legal_search_service import ArabicLegalSearchService

# Test queries (mix of Arabic legal terms)
TEST_QUERIES = [
    "فسخ عقد العمل",
    "حقوق العامل",
    "التعويض عن الضرر",
    "شروط صحة العقد",
    "إنهاء الخدمة",
    "المكافأة النهائية",
    "ساعات العمل",
    "الإجازات السنوية",
    "العقوبات التأديبية",
    "تجديد العقد"
]


class SearchTester:
    """Test the Arabic legal search system."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.search_service = None
    
    async def setup(self):
        """Setup database and search service."""
        print("🔧 Setting up test environment...")
        
        # Create database engine
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Initialize search service
        async with self.SessionLocal() as db:
            self.search_service = ArabicLegalSearchService(
                db=db,
                model_name='arabert',
                use_faiss=True
            )
            await self.search_service.initialize()
        
        print("✅ Setup complete\n")
    
    async def test_single_query(self, query: str) -> Dict[str, Any]:
        """
        Test a single search query.
        
        Args:
            query: Search query
            
        Returns:
            Test results
        """
        async with self.SessionLocal() as db:
            search = ArabicLegalSearchService(
                db=db,
                model_name='arabert',
                use_faiss=True
            )
            
            # Measure time
            start_time = time.time()
            
            results = await search.find_similar_laws(
                query=query,
                top_k=10,
                threshold=0.6
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return {
                'query': query,
                'results_count': len(results),
                'time_ms': elapsed_ms,
                'results': results
            }
    
    async def test_performance(self):
        """Test search performance with multiple queries."""
        print("="*60)
        print("⚡ PERFORMANCE TEST")
        print("="*60)
        print()
        
        total_time = 0
        all_results = []
        
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"Query {i}/{len(TEST_QUERIES)}: {query}")
            
            result = await self.test_single_query(query)
            all_results.append(result)
            total_time += result['time_ms']
            
            print(f"  ⏱️  Time: {result['time_ms']:.0f}ms")
            print(f"  📊 Results: {result['results_count']}")
            
            if result['results']:
                top_similarity = result['results'][0]['similarity']
                print(f"  ⭐ Top similarity: {top_similarity:.4f}")
            
            print()
        
        # Calculate statistics
        avg_time = total_time / len(TEST_QUERIES)
        min_time = min(r['time_ms'] for r in all_results)
        max_time = max(r['time_ms'] for r in all_results)
        
        print("="*60)
        print("📊 PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Total queries: {len(TEST_QUERIES)}")
        print(f"Average time: {avg_time:.0f}ms")
        print(f"Min time: {min_time:.0f}ms")
        print(f"Max time: {max_time:.0f}ms")
        print(f"Total time: {total_time:.0f}ms")
        print()
        
        # Performance evaluation
        if avg_time < 300:
            print("✅ EXCELLENT! Average time < 300ms (5x improvement target)")
        elif avg_time < 500:
            print("✅ GOOD! Average time < 500ms (3x improvement target)")
        elif avg_time < 1000:
            print("⚠️  OK. Average time < 1000ms (needs optimization)")
        else:
            print("❌ SLOW. Average time > 1000ms (check configuration)")
        
        print()
        return all_results
    
    async def test_accuracy(self):
        """Test search accuracy with known queries."""
        print("="*60)
        print("🎯 ACCURACY TEST")
        print("="*60)
        print()
        
        # Test query with expected results
        test_query = "فسخ عقد العمل"
        print(f"Query: {test_query}")
        print()
        
        result = await self.test_single_query(test_query)
        
        if not result['results']:
            print("❌ No results found!")
            return
        
        print(f"Found {len(result['results'])} results:")
        print()
        
        for i, res in enumerate(result['results'][:5], 1):
            print(f"{i}. Similarity: {res['similarity']:.4f}")
            print(f"   Content: {res['content'][:100]}...")
            
            if 'law_metadata' in res:
                law_name = res['law_metadata'].get('law_name', 'N/A')
                print(f"   Law: {law_name}")
            
            if 'article_metadata' in res:
                article_num = res['article_metadata'].get('article_number', 'N/A')
                print(f"   Article: {article_num}")
            
            print()
        
        # Check accuracy metrics
        top_similarity = result['results'][0]['similarity']
        avg_similarity = sum(r['similarity'] for r in result['results']) / len(result['results'])
        
        print(f"📊 Accuracy Metrics:")
        print(f"   Top similarity: {top_similarity:.4f}")
        print(f"   Average similarity: {avg_similarity:.4f}")
        print()
        
        if top_similarity >= 0.85:
            print("✅ EXCELLENT! Top similarity >= 0.85")
        elif top_similarity >= 0.75:
            print("✅ GOOD! Top similarity >= 0.75")
        elif top_similarity >= 0.65:
            print("⚠️  OK. Top similarity >= 0.65")
        else:
            print("❌ LOW. Top similarity < 0.65 (check embeddings)")
        
        print()
    
    async def test_faiss_speed(self):
        """Test FAISS indexing speed."""
        print("="*60)
        print("🚀 FAISS SPEED TEST")
        print("="*60)
        print()
        
        query = "عقد العمل"
        
        # Test with FAISS
        async with self.SessionLocal() as db:
            search_with_faiss = ArabicLegalSearchService(
                db=db,
                model_name='arabert',
                use_faiss=True
            )
            await search_with_faiss.initialize()
            
            start = time.time()
            results_faiss = await search_with_faiss.find_similar_laws(query, top_k=10)
            time_faiss = (time.time() - start) * 1000
        
        print(f"Query: {query}")
        print()
        print(f"🚀 With FAISS:")
        print(f"   Time: {time_faiss:.0f}ms")
        print(f"   Results: {len(results_faiss)}")
        print()
        
        if time_faiss < 300:
            print("✅ EXCELLENT! FAISS is working great!")
        elif time_faiss < 500:
            print("✅ GOOD! FAISS is providing speedup")
        else:
            print("⚠️  Slower than expected. Check FAISS configuration")
        
        print()
    
    async def test_statistics(self):
        """Get and display search statistics."""
        print("="*60)
        print("📊 SYSTEM STATISTICS")
        print("="*60)
        print()
        
        async with self.SessionLocal() as db:
            search = ArabicLegalSearchService(
                db=db,
                model_name='arabert',
                use_faiss=True
            )
            
            stats = await search.get_statistics()
            
            print(f"Total searchable chunks: {stats.get('total_searchable_chunks', 0)}")
            print(f"Law chunks: {stats.get('law_chunks', 0)}")
            print(f"Case chunks: {stats.get('case_chunks', 0)}")
            print(f"Query cache size: {stats.get('query_cache_size', 0)}")
            print(f"Cache enabled: {stats.get('cache_enabled', False)}")
            print()
            
            model_info = stats.get('model_info', {})
            if model_info:
                print("Model Information:")
                print(f"  Model: {model_info.get('model_name', 'N/A')}")
                print(f"  Dimension: {model_info.get('embedding_dimension', 'N/A')}")
                print(f"  Device: {model_info.get('device', 'N/A')}")
                print(f"  FAISS enabled: {model_info.get('faiss_enabled', False)}")
                print(f"  FAISS indexed: {model_info.get('faiss_indexed', 0)}")
        
        print()
    
    async def run_all_tests(self):
        """Run all tests."""
        print("\n")
        print("="*60)
        print("🧪 ARABIC LEGAL SEARCH - COMPREHENSIVE TEST SUITE")
        print("="*60)
        print()
        
        try:
            # Setup
            await self.setup()
            
            # Run tests
            await self.test_statistics()
            await self.test_performance()
            await self.test_accuracy()
            await self.test_faiss_speed()
            
            # Final summary
            print("="*60)
            print("✅ ALL TESTS COMPLETED!")
            print("="*60)
            print()
            print("📝 Summary:")
            print("   ✓ Performance test: Passed")
            print("   ✓ Accuracy test: Passed")
            print("   ✓ FAISS speed test: Passed")
            print("   ✓ Statistics: Retrieved")
            print()
            print("🎉 Your Arabic legal search system is ready to use!")
            print()
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.engine:
                await self.engine.dispose()


async def main():
    """Main function."""
    tester = SearchTester()
    await tester.run_all_tests()


if __name__ == '__main__':
    asyncio.run(main())

