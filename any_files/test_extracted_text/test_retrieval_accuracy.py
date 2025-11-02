"""
Test RAG Retrieval Accuracy

This script tests if the system retrieves the CORRECT and MOST RELEVANT laws
for given queries. This is critical for a RAG system!

We'll test queries against expected laws to measure accuracy.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, and_, or_
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeChunk, LawSource, LawArticle
from app.services.arabic_legal_search_service import ArabicLegalSearchService


# Test cases: query → expected law name
TEST_CASES = [
    {
        "query": "حقوق العامل",
        "expected_law": "نظام العمل السعودي",
        "description": "Worker's rights should return Saudi Labor Law"
    },
    {
        "query": "إنهاء عقد العمل",
        "expected_law": "نظام العمل السعودي", 
        "description": "Terminating employment contract should return Labor Law"
    },
    {
        "query": "الإجازات السنوية",
        "expected_law": "نظام العمل السعودي",
        "description": "Annual leave should return Labor Law"
    },
    {
        "query": "رواتب العمال وأجورهم",
        "expected_law": "نظام العمل السعودي",
        "description": "Worker salaries should return Labor Law"
    },
    {
        "query": "ساعات العمل اليومية",
        "expected_law": "نظام العمل السعودي",
        "description": "Working hours should return Labor Law"
    }
]


async def check_labor_law_in_database():
    """Check if Labor Law is actually in the database with embeddings."""
    print("=" * 80)
    print("1. CHECKING IF LABOR LAW EXISTS IN DATABASE")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # Find Labor Law
            query = select(LawSource).where(
                LawSource.name.like('%نظام العمل السعودي%')
            )
            result = await db.execute(query)
            labor_law = result.scalar_one_or_none()
            
            if not labor_law:
                print("❌ CRITICAL: Saudi Labor Law NOT FOUND in database!")
                print("   This means the law was never uploaded successfully.")
                return False
            
            print(f"✅ Found Labor Law: {labor_law.name}")
            print(f"   Law ID: {labor_law.id}")
            print(f"   Status: {labor_law.status}")
            
            # Count articles
            articles_query = select(LawArticle).where(
                LawArticle.law_source_id == labor_law.id
            )
            articles_result = await db.execute(articles_query)
            articles = articles_result.scalars().all()
            print(f"   Total Articles: {len(articles)}")
            
            # Count chunks with embeddings
            chunks_query = select(KnowledgeChunk).where(
                and_(
                    KnowledgeChunk.law_source_id == labor_law.id,
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != ''
                )
            )
            chunks_result = await db.execute(chunks_query)
            chunks = chunks_result.scalars().all()
            print(f"   Chunks with Embeddings: {len(chunks)}")
            
            if len(chunks) == 0:
                print("❌ CRITICAL: Labor Law has NO EMBEDDINGS!")
                print("   Articles exist but embeddings were not generated.")
                return False
            
            # Show sample content
            if chunks:
                sample = chunks[0]
                print(f"\n📄 Sample Chunk Content:")
                print(f"   {sample.content[:200]}...")
            
            print()
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_direct_similarity():
    """Test direct similarity between query and Labor Law chunks."""
    print("=" * 80)
    print("2. TESTING DIRECT SIMILARITY WITH LABOR LAW")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # Initialize search service
            search_service = ArabicLegalSearchService(db, use_faiss=True)
            await search_service.initialize()
            
            # Find Labor Law chunks
            labor_law_query = select(LawSource).where(
                LawSource.name.like('%نظام العمل السعودي%')
            )
            result = await db.execute(labor_law_query)
            labor_law = result.scalar_one_or_none()
            
            if not labor_law:
                print("❌ Labor Law not found")
                return
            
            # Get sample chunks from Labor Law
            chunks_query = select(KnowledgeChunk).where(
                and_(
                    KnowledgeChunk.law_source_id == labor_law.id,
                    KnowledgeChunk.embedding_vector.isnot(None)
                )
            ).limit(10)
            chunks_result = await db.execute(chunks_query)
            labor_chunks = chunks_result.scalars().all()
            
            # Test query
            query = "حقوق العامل"
            print(f"\n🔍 Query: '{query}'")
            print(f"📊 Testing against {len(labor_chunks)} Labor Law chunks")
            print("-" * 60)
            
            # Encode query
            query_embedding = search_service.embedding_service.encode_text(query)
            
            # Calculate similarities
            import json
            import numpy as np
            
            similarities = []
            for chunk in labor_chunks:
                try:
                    chunk_embedding = np.array(json.loads(chunk.embedding_vector))
                    similarity = search_service.embedding_service.cosine_similarity(
                        query_embedding,
                        chunk_embedding
                    )
                    similarities.append({
                        'chunk_id': chunk.id,
                        'similarity': similarity,
                        'content': chunk.content[:150]
                    })
                except:
                    continue
            
            # Sort by similarity
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            print(f"\nTop 5 most similar Labor Law chunks:")
            for i, sim in enumerate(similarities[:5], 1):
                print(f"\n[{i}] Similarity: {sim['similarity']:.4f}")
                print(f"    Chunk ID: {sim['chunk_id']}")
                print(f"    Content: {sim['content']}...")
            
            # Check if similarities are good enough
            if similarities:
                max_sim = similarities[0]['similarity']
                if max_sim < 0.4:
                    print(f"\n⚠️  WARNING: Highest similarity is {max_sim:.4f}")
                    print("   This is below threshold 0.4!")
                    print("   Possible issues:")
                    print("   1. Embeddings not capturing semantic meaning properly")
                    print("   2. Arabic text normalization too aggressive")
                    print("   3. Model not suitable for legal Arabic text")
                else:
                    print(f"\n✅ Good similarity scores (max: {max_sim:.4f})")
            
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def test_retrieval_accuracy():
    """Test full retrieval accuracy with expected results."""
    print("=" * 80)
    print("3. TESTING RAG RETRIEVAL ACCURACY")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # Initialize search service
            search_service = ArabicLegalSearchService(db, use_faiss=True)
            await search_service.initialize()
            
            total_tests = len(TEST_CASES)
            correct = 0
            incorrect = 0
            
            for test_case in TEST_CASES:
                query = test_case['query']
                expected_law = test_case['expected_law']
                description = test_case['description']
                
                print(f"\n{'='*60}")
                print(f"Test: {description}")
                print(f"Query: '{query}'")
                print(f"Expected Law: {expected_law}")
                print("-" * 60)
                
                # Search
                results = await search_service.find_similar_laws(
                    query=query,
                    top_k=10,
                    threshold=0.3,  # Use lower threshold for this test
                    use_fast_search=True
                )
                
                if not results:
                    print("❌ No results returned!")
                    incorrect += 1
                    continue
                
                # Check if expected law is in top results
                found_expected = False
                top_result_law = None
                
                for i, result in enumerate(results[:5], 1):  # Check top 5
                    law_name = result.get('law_metadata', {}).get('law_name', 'N/A')
                    
                    if i == 1:
                        top_result_law = law_name
                    
                    if expected_law in law_name:
                        found_expected = True
                        print(f"✅ CORRECT: Expected law found at rank {i}")
                        print(f"   Similarity: {result['similarity']:.4f}")
                        print(f"   Law: {law_name}")
                        if i == 1:
                            print(f"   ⭐ Top result is correct!")
                            correct += 1
                        else:
                            print(f"   ⚠️  But not the top result...")
                            incorrect += 1
                        break
                
                if not found_expected:
                    print(f"❌ INCORRECT: Expected law NOT in top 5!")
                    print(f"   Top result: {top_result_law}")
                    print(f"   Similarity: {results[0]['similarity']:.4f}")
                    incorrect += 1
                
                # Show top 3 results
                print(f"\n   Top 3 Results:")
                for i, result in enumerate(results[:3], 1):
                    law_name = result.get('law_metadata', {}).get('law_name', 'N/A')
                    print(f"   [{i}] {result['similarity']:.4f} - {law_name}")
            
            # Summary
            print(f"\n{'='*80}")
            print("ACCURACY SUMMARY")
            print(f"{'='*80}")
            print(f"Total Tests: {total_tests}")
            print(f"✅ Correct (top result): {correct}")
            print(f"❌ Incorrect: {incorrect}")
            accuracy = (correct / total_tests) * 100 if total_tests > 0 else 0
            print(f"📊 Accuracy: {accuracy:.1f}%")
            
            if accuracy < 80:
                print(f"\n❌ ACCURACY TOO LOW! Target is 100%")
                print(f"\n🔧 Possible Solutions:")
                print(f"   1. Use a better Arabic legal embedding model")
                print(f"   2. Fine-tune embeddings on Saudi legal corpus")
                print(f"   3. Improve chunk content (include more context)")
                print(f"   4. Adjust text normalization (might be too aggressive)")
                print(f"   5. Use hybrid search (semantic + keyword)")
            else:
                print(f"\n✅ Good accuracy!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run all accuracy tests."""
    print("\n" + "=" * 80)
    print("RAG RETRIEVAL ACCURACY TEST")
    print("Testing if system returns CORRECT laws for queries")
    print("=" * 80 + "\n")
    
    # Step 1: Check if Labor Law exists
    exists = await check_labor_law_in_database()
    
    if not exists:
        print("\n❌ Cannot continue: Labor Law not properly uploaded")
        return
    
    # Step 2: Test direct similarity
    await test_direct_similarity()
    
    # Step 3: Test full retrieval accuracy
    await test_retrieval_accuracy()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

