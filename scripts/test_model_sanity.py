"""Sanity check: test if model gives high similarity for identical text."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService

async def sanity_check():
    async with AsyncSessionLocal() as db:
        # Initialize embedding service
        embedding_service = ArabicLegalEmbeddingService(db, model_name='arabert', use_faiss=True)
        embedding_service.initialize_model()
        
        print("="*80)
        print("🧪 MODEL SANITY CHECK")
        print("="*80)
        
        # Test 1: Identical text
        text = "تزوير طابع"
        emb1 = embedding_service.encode_text(text)
        emb2 = embedding_service.encode_text(text)
        similarity = embedding_service.cosine_similarity(emb1, emb2)
        
        print(f"\n✅ Test 1: Identical Text")
        print(f"   Text: '{text}'")
        print(f"   Similarity: {similarity:.4f}")
        print(f"   Expected: 1.0000")
        print(f"   Status: {'✅ PASS' if similarity > 0.99 else '❌ FAIL'}")
        
        # Test 2: Similar text
        text1 = "تزوير طابع"
        text2 = "تزوير الطوابع"
        emb1 = embedding_service.encode_text(text1)
        emb2 = embedding_service.encode_text(text2)
        similarity = embedding_service.cosine_similarity(emb1, emb2)
        
        print(f"\n⚡ Test 2: Similar Text")
        print(f"   Text 1: '{text1}'")
        print(f"   Text 2: '{text2}'")
        print(f"   Similarity: {similarity:.4f}")
        print(f"   Expected: > 0.80")
        print(f"   Status: {'✅ PASS' if similarity > 0.80 else '❌ FAIL'}")
        
        # Test 3: Different text
        text1 = "تزوير طابع"
        text2 = "شراء سيارة"
        emb1 = embedding_service.encode_text(text1)
        emb2 = embedding_service.encode_text(text2)
        similarity = embedding_service.cosine_similarity(emb1, emb2)
        
        print(f"\n❌ Test 3: Different Text")
        print(f"   Text 1: '{text1}'")
        print(f"   Text 2: '{text2}'")
        print(f"   Similarity: {similarity:.4f}")
        print(f"   Expected: < 0.30")
        print(f"   Status: {'✅ PASS' if similarity < 0.30 else '❌ FAIL'}")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(sanity_check())

