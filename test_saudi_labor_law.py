"""
اختبار مباشر لتحليل ملف saudi_labor_law.json
"""

import asyncio
import json
from app.services.document_parser_service import LegalDocumentParser
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeDocument

async def test_json_parsing():
    """اختبار تحليل JSON مباشر"""
    
    print("🧪 اختبار تحليل ملف saudi_labor_law.json...")
    
    try:
        # قراءة الملف
        with open('data_set/files/saudi_labor_law.json', 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"✅ تم قراءة الملف بنجاح")
        print(f"📋 نوع البيانات: {type(json_data)}")
        print(f"📋 المفاتيح: {list(json_data.keys())}")
        
        # تحليل البنية
        if 'law_sources' in json_data:
            law_sources_value = json_data['law_sources']
            print(f"📋 law_sources نوع: {type(law_sources_value)}")
            
            if isinstance(law_sources_value, dict):
                print(f"📋 اسم المصدر: {law_sources_value.get('name', 'غير محدد')}")
                print(f"📋 نوع المصدر: {law_sources_value.get('type', 'غير محدد')}")
                
                if 'articles' in law_sources_value:
                    articles = law_sources_value['articles']
                    print(f"📋 عدد المواد: {len(articles)}")
                    print(f"📋 نوع المواد: {type(articles)}")
                    
                    # عرض أول 5 مواد
                    for i, article in enumerate(articles[:5]):
                        print(f"   المادة {i+1}: {article.get('article', 'غير محدد')}")
                        print(f"   النص: {article.get('text', 'غير محدد')[:50]}...")
                    
                    if len(articles) > 5:
                        print(f"   ... و {len(articles) - 5} مواد أخرى")
                else:
                    print("❌ لا توجد مواد في المصدر")
            else:
                print(f"❌ law_sources ليس dictionary: {type(law_sources_value)}")
        else:
            print("❌ لا يوجد law_sources في الملف")
        
        # اختبار التحليل مع قاعدة البيانات
        async with AsyncSessionLocal() as db:
            # إنشاء وثيقة تجريبية
            document = KnowledgeDocument(
                title="اختبار نظام العمل",
                category="law",
                file_path="data_set/files/saudi_labor_law.json",
                file_hash="test_hash_123",
                source_type='uploaded',
                status='raw',
                uploaded_by=1
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            print(f"\n🔄 بدء التحليل مع قاعدة البيانات...")
            print(f"📄 معرف الوثيقة: {document.id}")
            
            # تحليل الوثيقة
            parser = LegalDocumentParser(db)
            law_sources, articles, chunks = await parser.parse_document(
                "data_set/files/saudi_labor_law.json", 
                document, 
                {"filename": "saudi_labor_law.json"}
            )
            
            print(f"\n✅ نتائج التحليل:")
            print(f"   📚 مصادر قانونية: {len(law_sources)}")
            print(f"   📄 مواد: {len(articles)}")
            print(f"   📦 chunks: {len(chunks)}")
            
            # عرض تفاصيل المواد
            if articles:
                print(f"\n📋 تفاصيل المواد:")
                for i, article in enumerate(articles[:10]):  # أول 10 مواد
                    print(f"   {i+1}. {article.article_number}: {article.title or 'بدون عنوان'}")
                
                if len(articles) > 10:
                    print(f"   ... و {len(articles) - 10} مواد أخرى")
            
            # تنظيف البيانات التجريبية
            await db.delete(document)
            await db.commit()
            print(f"\n🧹 تم تنظيف البيانات التجريبية")
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_json_parsing())
