"""
Diagnostic script to test and debug the complete flow from JSON upload to search.
This script will help identify issues in the similar law retrieval process.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import (
    KnowledgeChunk, LawSource, LawArticle, KnowledgeDocument
)
from app.services.legal_laws_service import LegalLawsService
from app.services.arabic_legal_search_service import ArabicLegalSearchService


async def check_database_state():
    """Check the current state of the database."""
    print("=" * 80)
    print("1. CHECKING DATABASE STATE")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # Count law sources
            law_sources_query = select(func.count(LawSource.id))
            result = await db.execute(law_sources_query)
            law_sources_count = result.scalar() or 0
            print(f"✅ Total Law Sources: {law_sources_count}")
            
            # Count articles
            articles_query = select(func.count(LawArticle.id))
            result = await db.execute(articles_query)
            articles_count = result.scalar() or 0
            print(f"✅ Total Articles: {articles_count}")
            
            # Count chunks
            chunks_query = select(func.count(KnowledgeChunk.id))
            result = await db.execute(chunks_query)
            chunks_count = result.scalar() or 0
            print(f"✅ Total Chunks: {chunks_count}")
            
            # Count chunks with embeddings
            embedded_query = select(func.count(KnowledgeChunk.id)).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != ''
                )
            )
            result = await db.execute(embedded_query)
            embedded_count = result.scalar() or 0
            print(f"✅ Chunks with Embeddings: {embedded_count}/{chunks_count}")
            
            # Count law chunks with embeddings
            law_chunks_query = select(func.count(KnowledgeChunk.id)).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != '',
                    KnowledgeChunk.law_source_id.isnot(None)
                )
            )
            result = await db.execute(law_chunks_query)
            law_chunks_count = result.scalar() or 0
            print(f"✅ Law Chunks with Embeddings: {law_chunks_count}")
            
            # Get sample chunk to check embedding format
            if embedded_count > 0:
                sample_query = select(KnowledgeChunk).where(
                    and_(
                        KnowledgeChunk.embedding_vector.isnot(None),
                        KnowledgeChunk.embedding_vector != ''
                    )
                ).limit(1)
                result = await db.execute(sample_query)
                sample_chunk = result.scalar_one_or_none()
                
                if sample_chunk:
                    try:
                        embedding_data = json.loads(sample_chunk.embedding_vector)
                        print(f"\n📊 Sample Embedding Analysis:")
                        print(f"   - Chunk ID: {sample_chunk.id}")
                        print(f"   - Content Preview: {sample_chunk.content[:100]}...")
                        print(f"   - Embedding Type: {type(embedding_data)}")
                        print(f"   - Embedding Dimension: {len(embedding_data) if isinstance(embedding_data, list) else 'N/A'}")
                        print(f"   - Sample Values: {embedding_data[:5] if isinstance(embedding_data, list) else 'N/A'}")
                    except Exception as e:
                        print(f"⚠️  Failed to parse embedding: {e}")
            
            print()
            return {
                'law_sources': law_sources_count,
                'articles': articles_count,
                'chunks': chunks_count,
                'embedded_chunks': embedded_count,
                'law_chunks': law_chunks_count
            }
            
        except Exception as e:
            print(f"❌ Error checking database: {e}")
            return None


async def test_embedding_service():
    """Test the embedding service."""
    print("=" * 80)
    print("2. TESTING EMBEDDING SERVICE")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # Initialize search service
            search_service = ArabicLegalSearchService(db, use_faiss=True)
            
            # Check if model is initialized
            print("📥 Initializing embedding model...")
            search_service.embedding_service.initialize_model()
            
            # Get model info
            model_info = search_service.embedding_service.get_model_info()
            print(f"\n✅ Model Information:")
            print(f"   - Model Name: {model_info['model_name']}")
            print(f"   - Model Path: {model_info['model_path']}")
            print(f"   - Embedding Dimension: {model_info['embedding_dimension']}")
            print(f"   - Device: {model_info['device']}")
            print(f"   - FAISS Enabled: {model_info['faiss_enabled']}")
            print(f"   - FAISS Indexed Vectors: {model_info['faiss_indexed']}")
            
            # Test encoding
            test_text = "حقوق العامل في نظام العمل السعودي"
            print(f"\n🧪 Testing encoding with text: '{test_text}'")
            embedding = search_service.embedding_service.encode_text(test_text)
            print(f"✅ Encoding successful:")
            print(f"   - Embedding shape: {embedding.shape}")
            print(f"   - Embedding dimension: {len(embedding)}")
            print(f"   - Sample values: {embedding[:5]}")
            
            print()
            return model_info
            
        except Exception as e:
            print(f"❌ Error testing embedding service: {e}")
            import traceback
            traceback.print_exc()
            return None


async def test_faiss_index_build():
    """Test building FAISS index."""
    print("=" * 80)
    print("3. TESTING FAISS INDEX BUILD")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # Initialize search service
            search_service = ArabicLegalSearchService(db, use_faiss=True)
            
            # Initialize model first
            search_service.embedding_service.initialize_model()
            
            # Build FAISS index
            print("🔨 Building FAISS index...")
            index_result = await search_service.embedding_service.build_faiss_index()
            
            if index_result.get('success'):
                print(f"✅ FAISS index built successfully:")
                print(f"   - Total Vectors: {index_result.get('total_vectors', 0)}")
                print(f"   - Dimension: {index_result.get('dimension', 0)}")
                print(f"   - Chunks Indexed: {index_result.get('chunks_indexed', 0)}")
            else:
                print(f"❌ FAISS index build failed: {index_result.get('error')}")
            
            print()
            return index_result
            
        except Exception as e:
            print(f"❌ Error building FAISS index: {e}")
            import traceback
            traceback.print_exc()
            return None


async def test_search_functionality():
    """Test the search functionality."""
    print("=" * 80)
    print("4. TESTING SEARCH FUNCTIONALITY")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            # Initialize search service
            search_service = ArabicLegalSearchService(db, use_faiss=True)
            
            # Initialize the service (loads model and builds index)
            print("🚀 Initializing search service...")
            await search_service.initialize()
            
            # Test queries
            test_queries = [
                "حقوق العامل",
                "إنهاء عقد العمل",
                "الإجازات السنوية"
            ]
            
            for query in test_queries:
                print(f"\n🔍 Testing query: '{query}'")
                print("-" * 60)
                
                # Search similar laws
                results = await search_service.find_similar_laws(
                    query=query,
                    top_k=5,
                    threshold=0.5,
                    use_fast_search=True
                )
                
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"\n   Result {i}:")
                    print(f"   - Similarity: {result['similarity']:.4f}")
                    print(f"   - Chunk ID: {result['chunk_id']}")
                    print(f"   - Content: {result['content'][:150]}...")
                    
                    if 'law_metadata' in result:
                        print(f"   - Law: {result['law_metadata'].get('law_name', 'N/A')}")
                    
                    if 'article_metadata' in result:
                        print(f"   - Article: {result['article_metadata'].get('article_number', 'N/A')}")
                
                if len(results) == 0:
                    print("   ⚠️  No results found. This indicates a problem!")
            
            print()
            return True
            
        except Exception as e:
            print(f"❌ Error testing search: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_standard_vs_faiss_search():
    """Compare standard search vs FAISS search."""
    print("=" * 80)
    print("5. COMPARING SEARCH METHODS")
    print("=" * 80)
    
    async with AsyncSessionLocal() as db:
        try:
            query = "حقوق العامل"
            top_k = 5
            threshold = 0.5
            
            # Initialize search service
            search_service = ArabicLegalSearchService(db, use_faiss=True)
            await search_service.initialize()
            
            # Test FAISS search
            print(f"🔍 Testing FAISS search for: '{query}'")
            faiss_results = await search_service.find_similar_laws(
                query=query,
                top_k=top_k,
                threshold=threshold,
                use_fast_search=True
            )
            print(f"✅ FAISS Search: Found {len(faiss_results)} results")
            
            # Test standard search
            print(f"\n🔍 Testing standard search for: '{query}'")
            standard_results = await search_service.find_similar_laws(
                query=query,
                top_k=top_k,
                threshold=threshold,
                use_fast_search=False
            )
            print(f"✅ Standard Search: Found {len(standard_results)} results")
            
            # Compare
            print(f"\n📊 Comparison:")
            print(f"   - FAISS: {len(faiss_results)} results")
            print(f"   - Standard: {len(standard_results)} results")
            print(f"   - Difference: {abs(len(faiss_results) - len(standard_results))} results")
            
            if len(faiss_results) == 0 and len(standard_results) == 0:
                print("\n⚠️  CRITICAL: Both methods returned 0 results!")
                print("   This suggests:")
                print("   - No embeddings in database, OR")
                print("   - Embedding model not loaded, OR")
                print("   - Threshold too high, OR")
                print("   - Query encoding failed")
            
            print()
            return {
                'faiss_count': len(faiss_results),
                'standard_count': len(standard_results)
            }
            
        except Exception as e:
            print(f"❌ Error comparing searches: {e}")
            import traceback
            traceback.print_exc()
            return None


async def diagnose_search_issue():
    """Main diagnostic function."""
    print("\n" + "=" * 80)
    print("DIAGNOSTIC TEST: SIMILAR LAW SEARCH FLOW")
    print("=" * 80 + "\n")
    
    # Step 1: Check database state
    db_state = await check_database_state()
    
    if not db_state or db_state['embedded_chunks'] == 0:
        print("❌ ISSUE IDENTIFIED: No embeddings in database!")
        print("   Solution: Upload JSON files or regenerate embeddings.")
        return
    
    # Step 2: Test embedding service
    model_info = await test_embedding_service()
    
    if not model_info:
        print("❌ ISSUE IDENTIFIED: Embedding service failed to initialize!")
        return
    
    # Step 3: Test FAISS index build
    index_result = await test_faiss_index_build()
    
    if not index_result or not index_result.get('success'):
        print("⚠️  WARNING: FAISS index build failed! Will fall back to standard search.")
    
    # Step 4: Test search functionality
    search_success = await test_search_functionality()
    
    if not search_success:
        print("❌ ISSUE IDENTIFIED: Search functionality failed!")
        return
    
    # Step 5: Compare search methods
    comparison = await test_standard_vs_faiss_search()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print(f"  - Database State: {'✅ OK' if db_state else '❌ FAILED'}")
    print(f"  - Embedding Service: {'✅ OK' if model_info else '❌ FAILED'}")
    print(f"  - FAISS Index: {'✅ OK' if index_result and index_result.get('success') else '⚠️  WARNING'}")
    print(f"  - Search Function: {'✅ OK' if search_success else '❌ FAILED'}")
    
    if comparison:
        if comparison['faiss_count'] == 0 and comparison['standard_count'] == 0:
            print("\n❌ CRITICAL ISSUE: No search results returned!")
            print("   Root cause analysis:")
            print("   1. Check if embeddings are correctly formatted")
            print("   2. Verify embedding dimensions match between stored and model")
            print("   3. Lower threshold value")
            print("   4. Check query encoding")
        else:
            print(f"\n✅ Search is working! Found results with both methods.")


if __name__ == "__main__":
    asyncio.run(diagnose_search_issue())

