"""
اختبار Chroma مباشر
"""

import asyncio
from app.services.document_parser_service import VectorstoreManager

async def test_chroma_direct():
    """اختبار Chroma مباشر"""
    
    print("🧪 اختبار Chroma مباشر...")
    
    try:
        # إنشاء VectorstoreManager
        print("🔄 إنشاء VectorstoreManager...")
        manager = VectorstoreManager()
        
        print("✅ تم إنشاء VectorstoreManager بنجاح")
        
        # الحصول على vectorstore
        vectorstore = manager.get_vectorstore()
        print("✅ تم الحصول على vectorstore")
        
        # اختبار إضافة نص بسيط
        print("🔄 اختبار إضافة نص بسيط...")
        
        test_texts = [
            "هذا نص تجريبي للاختبار",
            "نظام العمل السعودي",
            "المادة الأولى من القانون"
        ]
        
        test_metadatas = [
            {"article": "المادة 1", "law_name": "نظام العمل"},
            {"article": "المادة 2", "law_name": "نظام العمل"},
            {"article": "المادة 3", "law_name": "نظام العمل"}
        ]
        
        # إضافة النصوص
        vectorstore.add_texts(
            texts=test_texts,
            metadatas=test_metadatas,
            ids=["test_1", "test_2", "test_3"]
        )
        
        # حفظ التغييرات
        vectorstore.persist()
        print("✅ تم إضافة النصوص إلى Chroma")
        
        # فحص العدد
        collection = vectorstore._collection
        count = collection.count()
        print(f"📊 عدد النصوص في Chroma: {count}")
        
        # اختبار البحث
        print("🔍 اختبار البحث...")
        results = vectorstore.similarity_search("عمل", k=2)
        print(f"📋 نتائج البحث:")
        for i, result in enumerate(results):
            print(f"   {i+1}. {result.page_content}")
            print(f"      Metadata: {result.metadata}")
        
        print("✅ اختبار Chroma نجح!")
        
    except Exception as e:
        print(f"❌ خطأ في اختبار Chroma: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chroma_direct())
