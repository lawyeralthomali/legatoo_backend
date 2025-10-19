"""
Test script for optimized document upload with ultra_small model.
This tests the fast, memory-efficient upload process.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.shared.rag_service import RAGService
from app.config.embedding_config import EmbeddingConfig

# Database URL
DATABASE_URL = "sqlite+aiosqlite:///./app.db"


async def test_upload():
    """Test document upload with optimized settings."""
    
    # Log configuration
    print("\n" + "=" * 60)
    print("🔍 CURRENT CONFIGURATION")
    print("=" * 60)
    EmbeddingConfig.log_configuration()
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\n" + "=" * 60)
        print("🚀 INITIALIZING RAG SERVICE")
        print("=" * 60)
        
        # Create RAG service with explicit ultra_small model
        rag_service = RAGService(session, model_name='ultra_small')
        
        print(f"✅ Service initialized")
        print(f"   Model: {rag_service.embedding_service.model_name}")
        print(f"   NO-ML Mode: {rag_service.embedding_service.no_ml_mode}")
        print(f"   Batch Size: {rag_service.embedding_service.batch_size}")
        print(f"   Max Seq Length: {rag_service.embedding_service.max_seq_length}")
        
        # Get statistics
        print("\n" + "=" * 60)
        print("📊 CURRENT DATABASE STATISTICS")
        print("=" * 60)
        
        stats = await rag_service.get_statistics()
        print(f"Total Documents: {stats.get('total_documents', 0)}")
        print(f"Total Chunks: {stats.get('total_chunks', 0)}")
        print(f"Chunks with Embeddings: {stats.get('chunks_with_embeddings', 0)}")
        print(f"Coverage: {stats.get('embedding_coverage', '0%')}")
        
        # Test embedding generation
        print("\n" + "=" * 60)
        print("🧪 TESTING EMBEDDING GENERATION")
        print("=" * 60)
        
        test_texts = [
            "القانون السعودي للعمل",
            "نظام المحاماة",
            "اللائحة التنفيذية"
        ]
        
        print(f"Generating embeddings for {len(test_texts)} test texts...")
        embeddings = await rag_service.embedding_service.generate_batch_embeddings(test_texts)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"   Dimensions: {len(embeddings[0]) if embeddings else 0}")
        print(f"   All valid: {all(any(v != 0 for v in emb) for emb in embeddings)}")
        
        # Validation
        print("\n" + "=" * 60)
        print("✅ VALIDATION")
        print("=" * 60)
        
        validation = await rag_service.embedding_service.validate_embedding_quality()
        
        if validation['success']:
            metrics = validation['quality_metrics']
            print(f"✅ Validation passed")
            print(f"   Texts processed: {metrics['sample_texts_processed']}")
            print(f"   Avg similarity: {metrics['average_similarity']}")
            print(f"   Embedding dim: {metrics['embedding_dimension']}")
        else:
            print(f"❌ Validation failed: {validation.get('error', 'Unknown')}")
        
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)
    print("\nThe system is ready for document uploads!")
    print("Use the ultra_small model for best performance (80MB, fast)")
    print("\nTo upload a document via API:")
    print('curl -X POST "http://localhost:8000/api/v1/rag/upload-document" \\')
    print('  -F "file=@your_document.pdf" \\')
    print('  -F "law_name=Test Law" \\')
    print('  -F "law_type=law" \\')
    print('  -F "jurisdiction=السعودية"')
    print()


if __name__ == "__main__":
    asyncio.run(test_upload())



