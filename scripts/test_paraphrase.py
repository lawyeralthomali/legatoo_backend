"""Test paraphrase-multilingual model (best multilingual model)."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService

async def test():
    async with AsyncSessionLocal() as db:
        print("Testing paraphrase-multilingual-mpnet (best for semantic search)...")
        svc = ArabicLegalEmbeddingService(db, model_name='paraphrase-multilingual')
        svc.initialize_model()
        print("✅ Model loaded!")
        
        # Sanity test
        print("\n🧪 Testing...")
        text1 = "تزوير طابع"
        text2 = "تزوير الطوابع"
        text3 = "شراء سيارة"
        
        emb1 = svc.encode_text(text1)
        emb2 = svc.encode_text(text2)
        emb3 = svc.encode_text(text3)
        
        sim_same = svc.cosine_similarity(emb1, emb1)
        sim_similar = svc.cosine_similarity(emb1, emb2)
        sim_different = svc.cosine_similarity(emb1, emb3)
        
        print(f"✅ Identical: {sim_same:.4f} (expected: 1.0000)")
        print(f"✅ Similar: {sim_similar:.4f} (expected: > 0.70)")
        print(f"❌ Different: {sim_different:.4f} (expected: < 0.50)")
        
        # Test with real legal query
        query = "عقوبة تزوير الطوابع"
        chunk = "**تزوير طابع**\n\nمن **زور طابعاً** يعاقب **بالسجن مدة لا تتجاوز خمس سنوات**"
        
        emb_q = svc.encode_text(query)
        emb_c = svc.encode_text(chunk)
        sim_legal = svc.cosine_similarity(emb_q, emb_c)
        
        print(f"\n🔍 Legal query similarity: {sim_legal:.4f} (expected: > 0.70)")
        
        print(f"\nEmbedding dimension: {len(emb1)}")
        
        if sim_similar > 0.70 and sim_different < 0.50 and sim_legal > 0.70:
            print("\n🎉 SUCCESS! This model works PERFECTLY for Arabic legal search!")
        elif sim_legal > 0.60:
            print("\n✅ GOOD! This model works well enough for Arabic")
        else:
            print("\n⚠️ Results not ideal")

if __name__ == "__main__":
    asyncio.run(test())

