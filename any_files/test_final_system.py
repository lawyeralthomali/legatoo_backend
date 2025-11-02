"""
اختبار نهائي للنظام الجديد مع معالجة جميع المواد
"""

import asyncio
import json
from app.services.document_parser_service import DocumentUploadService
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import LawArticle, LawSource, KnowledgeChunk, KnowledgeDocument
from sqlalchemy import select

async def test_complete_system():
    """اختبار النظام الكامل"""
    
    print("🚀 اختبار النظام الكامل مع معالجة جميع المواد...")
    
    try:
        # قراءة الملف
        with open('data_set/files/saudi_labor_law.json', 'rb') as f:
            file_content = f.read()
        
        print(f"✅ تم قراءة الملف: {len(file_content)} بايت")
        
        async with AsyncSessionLocal() as db:
            # إنشاء خدمة الرفع
            upload_service = DocumentUploadService(db)
            
            print("🔄 بدء رفع الوثيقة...")
            
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
            
            # فحص النتائج في قاعدة البيانات
            print(f"\n🔍 فحص النتائج في قاعدة البيانات...")
            
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
                for i, article in enumerate(articles[:10]):
                    print(f"   {i+1}. {article.article_number}: {article.content[:50]}...")
                
                if len(articles) > 10:
                    print(f"   ... و {len(articles) - 10} مواد أخرى")
            
            # فحص Chroma
            print(f"\n🔍 فحص Chroma Vectorstore...")
            try:
                vectorstore = upload_service.dual_db_manager.vectorstore
                collection = vectorstore._collection
                chroma_count = collection.count()
                print(f"📊 عدد الـ chunks في Chroma: {chroma_count}")
                
                if chroma_count > 0:
                    print(f"✅ Chroma يحتوي على البيانات!")
                else:
                    print(f"⚠️ Chroma فارغ!")
                    
            except Exception as chroma_error:
                print(f"❌ خطأ في فحص Chroma: {chroma_error}")
            
            # فحص التزامن
            print(f"\n🔄 فحص التزامن بين النظامين...")
            if len(chunks) == chroma_count:
                print(f"✅ النظامان متزامنان: {len(chunks)} chunks في كل منهما")
            else:
                print(f"⚠️ عدم تزامن: SQL={len(chunks)}, Chroma={chroma_count}")
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_system())
