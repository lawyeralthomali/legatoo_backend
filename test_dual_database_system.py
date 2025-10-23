"""
اختبار النظام الجديد مع دعم قاعدة البيانات المزدوجة
"""

import asyncio
import json
import requests
from app.services.document_parser_service import (
    VectorstoreManager, 
    DualDatabaseManager, 
    LegalDocumentParser,
    DocumentUploadService
)
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeDocument, KnowledgeChunk

async def test_vectorstore_manager():
    """اختبار VectorstoreManager (Singleton)"""
    print("🧪 اختبار VectorstoreManager...")
    
    # إنشاء مثيلين للتأكد من Singleton
    manager1 = VectorstoreManager()
    manager2 = VectorstoreManager()
    
    # التأكد من أنهما نفس المثيل
    assert manager1 is manager2, "❌ VectorstoreManager ليس Singleton!"
    print("✅ VectorstoreManager Singleton يعمل بشكل صحيح")
    
    # اختبار المكونات
    vectorstore = manager1.get_vectorstore()
    embeddings = manager1.get_embeddings()
    text_splitter = manager1.get_text_splitter()
    
    assert vectorstore is not None, "❌ Vectorstore غير موجود"
    assert embeddings is not None, "❌ Embeddings غير موجود"
    assert text_splitter is not None, "❌ Text splitter غير موجود"
    
    print("✅ جميع مكونات VectorstoreManager تعمل بشكل صحيح")

async def test_dual_database_manager():
    """اختبار DualDatabaseManager"""
    print("\n🧪 اختبار DualDatabaseManager...")
    
    async with AsyncSessionLocal() as db:
        dual_manager = DualDatabaseManager(db)
        
        # اختبار إضافة chunk تجريبي
        test_chunk = KnowledgeChunk(
            document_id=1,
            chunk_index=0,
            content="هذا نص تجريبي للاختبار",
            tokens_count=10,
            verified_by_admin=False
        )
        
        test_metadata = {
            "test": True,
            "article_number": "المادة 1",
            "law_name": "قانون تجريبي"
        }
        
        # محاولة إضافة chunk (قد تفشل إذا لم يكن هناك document_id=1)
        try:
            success = await dual_manager.add_chunk_to_both_databases(
                test_chunk, test_chunk.content, test_metadata
            )
            if success:
                print("✅ إضافة chunk إلى كلا النظامين نجحت")
                
                # اختبار حذف chunk
                delete_success = await dual_manager.delete_chunk_from_both_databases(test_chunk.id)
                if delete_success:
                    print("✅ حذف chunk من كلا النظامين نجح")
                else:
                    print("⚠️ حذف chunk فشل")
            else:
                print("⚠️ إضافة chunk فشلت (ربما بسبب عدم وجود document_id=1)")
        except Exception as e:
            print(f"⚠️ اختبار إضافة chunk فشل: {e}")
        
        # اختبار مزامنة النظامين
        try:
            sync_stats = await dual_manager.sync_database_states()
            print(f"✅ مزامنة النظامين نجحت: {sync_stats}")
        except Exception as e:
            print(f"⚠️ مزامنة النظامين فشلت: {e}")

async def test_document_parser():
    """اختبار LegalDocumentParser المحدث"""
    print("\n🧪 اختبار LegalDocumentParser...")
    
    async with AsyncSessionLocal() as db:
        parser = LegalDocumentParser(db)
        
        # اختبار وجود dual_db_manager
        assert parser.dual_db_manager is not None, "❌ dual_db_manager غير موجود"
        print("✅ LegalDocumentParser تم تحديثه بنجاح")
        
        # اختبار text splitter
        test_text = "هذا نص طويل للاختبار. يحتوي على عدة جمل. يجب تقسيمه إلى chunks متعددة."
        chunks = parser.dual_db_manager.text_splitter.split_text(test_text)
        
        assert len(chunks) > 0, "❌ Text splitter لا يعمل"
        print(f"✅ Text splitter يعمل: تم تقسيم النص إلى {len(chunks)} chunks")

async def test_document_upload_service():
    """اختبار DocumentUploadService المحدث"""
    print("\n🧪 اختبار DocumentUploadService...")
    
    async with AsyncSessionLocal() as db:
        service = DocumentUploadService(db)
        
        # اختبار وجود dual_db_manager
        assert service.dual_db_manager is not None, "❌ dual_db_manager غير موجود"
        print("✅ DocumentUploadService تم تحديثه بنجاح")
        
        # اختبار الحصول على حالة النظامين
        try:
            status = await service.get_database_status()
            print(f"✅ حالة النظامين: {status}")
        except Exception as e:
            print(f"⚠️ فشل في الحصول على حالة النظامين: {e}")

def test_api_endpoints():
    """اختبار API endpoints الجديدة"""
    print("\n🧪 اختبار API endpoints الجديدة...")
    
    base_url = "http://localhost:8000"
    
    # اختبار حالة النظامين
    try:
        response = requests.get(f"{base_url}/api/v1/documents/database/status")
        if response.status_code == 200:
            print("✅ GET /database/status يعمل")
            data = response.json()
            print(f"📊 حالة النظامين: {data.get('data', {}).get('synchronization', {})}")
        else:
            print(f"⚠️ GET /database/status فشل: {response.status_code}")
    except Exception as e:
        print(f"⚠️ اختبار API فشل: {e}")
    
    # اختبار مزامنة النظامين
    try:
        response = requests.post(f"{base_url}/api/v1/documents/database/sync")
        if response.status_code == 200:
            print("✅ POST /database/sync يعمل")
        else:
            print(f"⚠️ POST /database/sync فشل: {response.status_code}")
    except Exception as e:
        print(f"⚠️ اختبار مزامنة API فشل: {e}")

async def test_json_parsing_with_dual_db():
    """اختبار تحليل JSON مع قاعدة البيانات المزدوجة"""
    print("\n🧪 اختبار تحليل JSON مع قاعدة البيانات المزدوجة...")
    
    # بيانات JSON تجريبية
    test_json_data = {
        "law_sources": {
            "name": "قانون تجريبي",
            "type": "law",
            "jurisdiction": "المملكة العربية السعودية",
            "issuing_authority": "وزارة التجارة",
            "issue_date": "2024-01-01",
            "articles": [
                {
                    "article": "المادة 1",
                    "title": "تعريفات",
                    "text": "هذا نص المادة الأولى من القانون التجريبي. يحتوي على تعريفات مهمة للقانون.",
                    "order_index": 1
                },
                {
                    "article": "المادة 2",
                    "title": "التطبيق",
                    "text": "هذا نص المادة الثانية من القانون التجريبي. يتحدث عن تطبيق القانون.",
                    "order_index": 2
                }
            ]
        }
    }
    
    # حفظ البيانات في ملف تجريبي
    test_file_path = "test_dual_db_document.json"
    with open(test_file_path, 'w', encoding='utf-8') as f:
        json.dump(test_json_data, f, ensure_ascii=False, indent=2)
    
    try:
        async with AsyncSessionLocal() as db:
            # إنشاء وثيقة تجريبية
            document = KnowledgeDocument(
                title="وثيقة تجريبية",
                category="law",
                file_path=test_file_path,
                file_hash="test_hash",
                source_type='uploaded',
                status='raw',
                uploaded_by=1
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # اختبار التحليل
            parser = LegalDocumentParser(db)
            law_sources, articles, chunks = await parser.parse_document(
                test_file_path, document, {"filename": "test.json"}
            )
            
            print(f"✅ تحليل JSON نجح:")
            print(f"   - مصادر قانونية: {len(law_sources)}")
            print(f"   - مواد: {len(articles)}")
            print(f"   - chunks: {len(chunks)}")
            
            # تنظيف البيانات التجريبية
            await db.delete(document)
            await db.commit()
            
    except Exception as e:
        print(f"❌ اختبار تحليل JSON فشل: {e}")
    
    finally:
        # حذف الملف التجريبي
        import os
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

async def main():
    """تشغيل جميع الاختبارات"""
    print("🚀 بدء اختبار النظام الجديد مع دعم قاعدة البيانات المزدوجة\n")
    
    try:
        await test_vectorstore_manager()
        await test_dual_database_manager()
        await test_document_parser()
        await test_document_upload_service()
        await test_json_parsing_with_dual_db()
        
        print("\n" + "="*60)
        print("🎉 جميع الاختبارات الأساسية مكتملة!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ خطأ في الاختبارات: {e}")
    
    # اختبار API endpoints (يتطلب تشغيل الخادم)
    print("\n📡 اختبار API endpoints...")
    test_api_endpoints()

if __name__ == "__main__":
    asyncio.run(main())
