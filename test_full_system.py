"""
تنظيف قاعدة البيانات واختبار النظام الجديد
"""

import asyncio
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import LawArticle, LawSource, KnowledgeChunk, KnowledgeDocument
from sqlalchemy import delete

async def clean_database():
    """تنظيف قاعدة البيانات"""
    
    print("🧹 تنظيف قاعدة البيانات...")
    
    async with AsyncSessionLocal() as db:
        try:
            # حذف جميع البيانات
            await db.execute(delete(KnowledgeChunk))
            await db.execute(delete(LawArticle))
            await db.execute(delete(LawSource))
            await db.execute(delete(KnowledgeDocument))
            
            await db.commit()
            print("✅ تم تنظيف قاعدة البيانات بنجاح")
            
        except Exception as e:
            print(f"❌ خطأ في تنظيف قاعدة البيانات: {e}")
            await db.rollback()

async def test_upload():
    """اختبار رفع الملف"""
    
    print("\n🚀 اختبار رفع ملف saudi_labor_law.json...")
    
    try:
        from app.services.document_parser_service import DocumentUploadService
        
        async with AsyncSessionLocal() as db:
            # قراءة الملف
            with open('data_set/files/saudi_labor_law.json', 'rb') as f:
                file_content = f.read()
            
            # إنشاء خدمة الرفع
            upload_service = DocumentUploadService(db)
            
            # رفع الوثيقة
            result = await upload_service.upload_document(
                file_content=file_content,
                filename="saudi_labor_law.json",
                title="نظام العمل السعودي",
                category="law",
                uploaded_by=1
            )
            
            print(f"✅ تم رفع الوثيقة بنجاح!")
            print(f"📄 معرف الوثيقة: {result['document_id']}")
            print(f"📚 مصادر قانونية: {result['law_sources_processed']}")
            print(f"📄 مواد: {result['articles_processed']}")
            print(f"📦 chunks: {result['chunks_created']}")
            
    except Exception as e:
        print(f"❌ خطأ في رفع الوثيقة: {e}")
        import traceback
        traceback.print_exc()

async def check_results():
    """فحص النتائج"""
    
    print("\n🔍 فحص النتائج...")
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        
        # فحص المصادر القانونية
        sources_result = await db.execute(select(LawSource))
        sources = sources_result.scalars().all()
        print(f"📚 عدد المصادر القانونية: {len(sources)}")
        
        # فحص المواد
        articles_result = await db.execute(select(LawArticle))
        articles = articles_result.scalars().all()
        print(f"📄 عدد المواد: {len(articles)}")
        
        # فحص الـ chunks
        chunks_result = await db.execute(select(KnowledgeChunk))
        chunks = chunks_result.scalars().all()
        print(f"📦 عدد الـ chunks: {len(chunks)}")
        
        # عرض بعض المواد
        if articles:
            print(f"\n📋 بعض المواد:")
            for i, article in enumerate(articles[:5]):
                print(f"   {i+1}. {article.article_number}: {article.content[:50]}...")
            
            if len(articles) > 5:
                print(f"   ... و {len(articles) - 5} مواد أخرى")

async def main():
    """تشغيل الاختبار الكامل"""
    
    print("🚀 بدء الاختبار الكامل للنظام الجديد\n")
    
    # تنظيف قاعدة البيانات
    await clean_database()
    
    # اختبار الرفع
    await test_upload()
    
    # فحص النتائج
    await check_results()
    
    print("\n🎉 انتهى الاختبار!")

if __name__ == "__main__":
    asyncio.run(main())
