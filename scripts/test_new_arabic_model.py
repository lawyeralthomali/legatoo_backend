"""اختبار الموديل العربي الجديد للـ embeddings."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService

async def test_new_model():
    async with AsyncSessionLocal() as db:
        # تحميل الموديل الجديد
        print("="*80)
        print("🧪 اختبار الموديل العربي الجديد (AraBERT Sentence Transformer)")
        print("="*80)
        
        embedding_service = ArabicLegalEmbeddingService(db, model_name='arabert-st', use_faiss=True)
        
        print("\n📥 جاري تحميل الموديل...")
        try:
            embedding_service.initialize_model()
        except Exception as e:
            print(f"\n❌ فشل تحميل الموديل: {str(e)}")
            print("\n💡 جرب موديل بديل:")
            print("   - arabic-st: asafaya/bert-base-arabic-sentence-embedding")
            print("   - labse: sentence-transformers/LaBSE")
            print("   - paraphrase-multilingual: sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
            return
        
        print("\n" + "="*80)
        print("✅ TEST 1: نص متطابق")
        print("="*80)
        
        text = "تزوير طابع"
        emb1 = embedding_service.encode_text(text)
        emb2 = embedding_service.encode_text(text)
        similarity = embedding_service.cosine_similarity(emb1, emb2)
        
        print(f"النص: '{text}'")
        print(f"التشابه: {similarity:.4f}")
        print(f"المتوقع: 1.0000")
        status = "✅ نجح" if similarity > 0.99 else "❌ فشل"
        print(f"النتيجة: {status}")
        
        print("\n" + "="*80)
        print("✅ TEST 2: نصوص متشابهة")
        print("="*80)
        
        text1 = "تزوير طابع"
        text2 = "تزوير الطوابع"
        emb1 = embedding_service.encode_text(text1)
        emb2 = embedding_service.encode_text(text2)
        similarity = embedding_service.cosine_similarity(emb1, emb2)
        
        print(f"النص 1: '{text1}'")
        print(f"النص 2: '{text2}'")
        print(f"التشابه: {similarity:.4f}")
        print(f"المتوقع: > 0.80")
        status = "✅ نجح" if similarity > 0.80 else "❌ فشل"
        print(f"النتيجة: {status}")
        
        print("\n" + "="*80)
        print("❌ TEST 3: نصوص مختلفة")
        print("="*80)
        
        text1 = "تزوير طابع"
        text2 = "شراء سيارة"
        emb1 = embedding_service.encode_text(text1)
        emb2 = embedding_service.encode_text(text2)
        similarity = embedding_service.cosine_similarity(emb1, emb2)
        
        print(f"النص 1: '{text1}'")
        print(f"النص 2: '{text2}'")
        print(f"التشابه: {similarity:.4f}")
        print(f"المتوقع: < 0.30")
        status = "✅ نجح" if similarity < 0.30 else "❌ فشل"
        print(f"النتيجة: {status}")
        
        print("\n" + "="*80)
        print("🔍 TEST 4: استعلام قانوني حقيقي")
        print("="*80)
        
        query = "عقوبة تزوير الطوابع"
        chunk_content = "**تزوير طابع**\n\nمن **زور طابعاً** يعاقب **بالسجن مدة لا تتجاوز خمس سنوات**"
        
        emb1 = embedding_service.encode_text(query)
        emb2 = embedding_service.encode_text(chunk_content)
        similarity = embedding_service.cosine_similarity(emb1, emb2)
        
        print(f"الاستعلام: '{query}'")
        print(f"المستند: '{chunk_content[:50]}...'")
        print(f"التشابه: {similarity:.4f}")
        print(f"المتوقع: > 0.70")
        status = "✅ نجح" if similarity > 0.70 else "❌ فشل"
        print(f"النتيجة: {status}")
        
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"بعد التضمين: {embedding_service.embedding_dimension}")
        print(f"نوع الموديل: {embedding_service.model_type}")
        print(f"الموديل: {embedding_service.model_name}")
        print("="*80)

if __name__ == "__main__":
    asyncio.run(test_new_model())

