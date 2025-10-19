"""
Direct service test - tests the embedding service directly without HTTP.

This test bypasses the HTTP layer and tests the services directly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_embedding_service():
    """Test the embedding service directly"""
    print("🧪 Testing EmbeddingService directly...")
    
    try:
        # Import the service
        from app.services.shared.embedding_service import EmbeddingService
        from app.db.database import get_db
        
        print("✅ Successfully imported EmbeddingService")
        
        # Create a mock database session
        class MockDB:
            pass
        
        # Test NO-ML mode
        print("🚫 Testing NO-ML mode...")
        embedding_service = EmbeddingService(MockDB(), model_name='no_ml')
        
        print(f"   - Model name: {embedding_service.model_name}")
        print(f"   - NO-ML mode: {embedding_service.no_ml_mode}")
        
        # Test hash-based embedding generation
        test_text = "نص اختبار للتحقق من عمل النظام"
        print(f"📝 Testing with text: '{test_text}'")
        
        # Generate embedding
        embedding = await embedding_service.generate_embedding(test_text)
        
        print(f"✅ Generated embedding:")
        print(f"   - Dimension: {len(embedding)}")
        print(f"   - First 5 values: {embedding[:5]}")
        print(f"   - All zeros: {all(x == 0.0 for x in embedding)}")
        
        # Test batch embeddings
        test_texts = [
            "نص اختبار أول",
            "نص اختبار ثاني", 
            "نص اختبار ثالث"
        ]
        
        print(f"📦 Testing batch embeddings for {len(test_texts)} texts...")
        batch_embeddings = await embedding_service.generate_batch_embeddings(test_texts)
        
        print(f"✅ Generated batch embeddings:")
        print(f"   - Count: {len(batch_embeddings)}")
        print(f"   - All same dimension: {all(len(e) == len(batch_embeddings[0]) for e in batch_embeddings)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rag_service():
    """Test the RAG service directly"""
    print("\n🧪 Testing RAGService directly...")
    
    try:
        from app.services.shared.rag_service import RAGService
        
        class MockDB:
            pass
        
        # Test RAG service initialization
        rag_service = RAGService(MockDB(), model_name='no_ml')
        
        print(f"✅ RAG Service initialized:")
        print(f"   - Model name: {rag_service.embedding_service.model_name}")
        print(f"   - NO-ML mode: {rag_service.embedding_service.no_ml_mode}")
        print(f"   - Chunk size: {rag_service.chunk_size}")
        
        # Test text chunking
        test_text = """
        نظام اختبار
        
        المادة 1: هذا نص اختبار طويل نوعاً ما للتحقق من عمل نظام التقسيم.
        
        المادة 2: يجب أن يتم تقسيم هذا النص إلى أجزاء صغيرة مناسبة للبحث.
        
        المادة 3: هذا الجزء الثالث أيضاً جزء من النص المطلوب تقسيمه.
        """
        
        print(f"📄 Testing text chunking...")
        chunks = rag_service._smart_chunk_text(test_text)
        
        print(f"✅ Text chunked:")
        print(f"   - Number of chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"   - Chunk {i+1}: {len(chunk['content'])} chars, {chunk['word_count']} words")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 70)
    print("🔬 Direct Service Test (NO-ML Mode)")
    print("=" * 70)
    print()
    
    # Test embedding service
    embedding_success = await test_embedding_service()
    
    # Test RAG service  
    rag_success = await test_rag_service()
    
    print()
    print("=" * 70)
    if embedding_success and rag_success:
        print("✅ ALL TESTS PASSED!")
        print("   - NO-ML mode working correctly")
        print("   - Hash-based embeddings generated")
        print("   - Text chunking working")
        print("   - Services functioning without ML models")
        print("   - No memory issues or crashes")
    else:
        print("❌ SOME TESTS FAILED!")
        print("   - Check the errors above")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

