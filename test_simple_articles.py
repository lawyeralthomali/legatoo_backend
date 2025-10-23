"""
اختبار بسيط لمعالجة جميع المواد
"""

import asyncio
import json
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeDocument, LawSource, LawArticle
from app.services.document_parser_service import LegalDocumentParser

async def test_article_processing():
    """اختبار معالجة المواد"""
    
    print("🧪 اختبار معالجة المواد...")
    
    try:
        # قراءة الملف
        with open('data_set/files/saudi_labor_law.json', 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"✅ تم قراءة الملف: {len(json_data['law_sources']['articles'])} مادة")
        
        async with AsyncSessionLocal() as db:
            # إنشاء وثيقة
            document = KnowledgeDocument(
                title="اختبار نظام العمل",
                category="law",
                file_path="test.json",
                file_hash="test_hash",
                source_type='uploaded',
                status='raw',
                uploaded_by=1
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # إنشاء مصدر قانوني
            law_source = LawSource(
                name="نظام العمل",
                type="law",
                jurisdiction="المملكة العربية السعودية",
                knowledge_document_id=document.id,
                status='processed'
            )
            
            db.add(law_source)
            await db.commit()
            await db.refresh(law_source)
            
            print(f"✅ تم إنشاء المصدر القانوني: {law_source.id}")
            
            # معالجة المواد
            articles_data = json_data['law_sources']['articles']
            processed_count = 0
            
            for i, article_data in enumerate(articles_data):
                try:
                    # إنشاء مادة
                    article = LawArticle(
                        law_source_id=law_source.id,
                        article_number=article_data.get('article'),
                        title=article_data.get('title'),
                        content=article_data['text'],
                        order_index=i,
                        source_document_id=document.id
                    )
                    
                    db.add(article)
                    await db.commit()
                    await db.refresh(article)
                    
                    processed_count += 1
                    
                    if processed_count % 50 == 0:
                        print(f"📄 تم معالجة {processed_count} مادة...")
                        
                except Exception as e:
                    print(f"❌ خطأ في المادة {i+1}: {e}")
                    continue
            
            print(f"✅ تم معالجة {processed_count} مادة بنجاح")
            
            # فحص النتائج
            from sqlalchemy import select
            articles_result = await db.execute(select(LawArticle))
            articles = articles_result.scalars().all()
            
            print(f"📊 عدد المواد في قاعدة البيانات: {len(articles)}")
            
            # عرض بعض المواد
            for i, article in enumerate(articles[:5]):
                print(f"   {i+1}. {article.article_number}: {article.content[:50]}...")
            
            # تنظيف
            await db.delete(document)
            await db.commit()
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_article_processing())
