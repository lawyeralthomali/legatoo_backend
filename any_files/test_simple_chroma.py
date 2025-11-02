"""
اختبار مبسط لمعالجة المواد مع Chroma
"""

import asyncio
import json
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeDocument, LawSource, LawArticle, KnowledgeChunk
from app.services.document_parser_service import VectorstoreManager

async def test_simple_chroma():
    """اختبار مبسط مع Chroma"""
    
    print("🧪 اختبار مبسط مع Chroma...")
    
    try:
        # قراءة الملف
        with open('data_set/files/saudi_labor_law.json', 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"✅ تم قراءة الملف: {len(json_data['law_sources']['articles'])} مادة")
        
        async with AsyncSessionLocal() as db:
            # إنشاء وثيقة
            document = KnowledgeDocument(
                title="نظام العمل السعودي",
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
            
            print(f"✅ تم إنشاء الوثيقة: {document.id}")
            
            # إنشاء مصدر قانوني
            law_source_data = json_data['law_sources']
            law_source = LawSource(
                name=law_source_data['name'],
                type=law_source_data['type'],
                jurisdiction=law_source_data['jurisdiction'],
                issuing_authority=law_source_data['issuing_authority'],
                knowledge_document_id=document.id,
                status='processed'
            )
            
            db.add(law_source)
            await db.commit()
            await db.refresh(law_source)
            
            print(f"✅ تم إنشاء المصدر القانوني: {law_source.id}")
            
            # معالجة المواد الأولى فقط للاختبار
            articles_data = law_source_data['articles'][:3]  # أول 3 مواد فقط
            processed_count = 0
            
            print(f"🔄 بدء معالجة {len(articles_data)} مادة...")
            
            # إنشاء VectorstoreManager
            vectorstore_manager = VectorstoreManager()
            vectorstore = vectorstore_manager.get_vectorstore()
            
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
                    print(f"📄 تم معالجة المادة {i+1}: {article.article_number}")
                    
                    # إنشاء chunk بسيط
                    try:
                        chunk = KnowledgeChunk(
                            document_id=document.id,
                            chunk_index=0,
                            content=article.content,
                            tokens_count=len(article.content.split()),
                            law_source_id=law_source.id,
                            article_id=article.id,
                            order_index=0,
                            verified_by_admin=False
                        )
                        
                        db.add(chunk)
                        await db.commit()
                        await db.refresh(chunk)
                        
                        print(f"📦 تم إنشاء chunk {chunk.id} للمادة {article.article_number}")
                        
                        # إضافة إلى Chroma
                        try:
                            metadata = {
                                "article": article.article_number,
                                "law_name": law_source.name,
                                "law_type": law_source.type,
                                "jurisdiction": law_source.jurisdiction,
                                "document_title": document.title
                            }
                            
                            vectorstore.add_texts(
                                texts=[article.content],
                                metadatas=[metadata],
                                ids=[str(chunk.id)]
                            )
                            
                            vectorstore.persist()
                            print(f"✅ تم إضافة chunk {chunk.id} إلى Chroma")
                            
                        except Exception as chroma_error:
                            print(f"❌ خطأ في إضافة chunk إلى Chroma: {chroma_error}")
                            
                    except Exception as chunk_error:
                        print(f"❌ خطأ في إنشاء chunk: {chunk_error}")
                        
                except Exception as e:
                    print(f"❌ خطأ في المادة {i+1}: {e}")
                    continue
            
            print(f"✅ تم معالجة {processed_count} مادة بنجاح")
            
            # فحص النتائج
            from sqlalchemy import select
            articles_result = await db.execute(select(LawArticle))
            articles = articles_result.scalars().all()
            
            chunks_result = await db.execute(select(KnowledgeChunk))
            chunks = chunks_result.scalars().all()
            
            print(f"\n📊 النتائج النهائية:")
            print(f"📄 عدد المواد في قاعدة البيانات: {len(articles)}")
            print(f"📦 عدد الـ chunks في قاعدة البيانات: {len(chunks)}")
            
            # فحص Chroma
            try:
                collection = vectorstore._collection
                chroma_count = collection.count()
                print(f"📊 عدد الـ chunks في Chroma: {chroma_count}")
                
                if chroma_count > 0:
                    print(f"✅ Chroma يحتوي على البيانات!")
                    
                    # اختبار البحث
                    try:
                        results = vectorstore.similarity_search("عمل", k=2)
                        print(f"🔍 نتائج البحث:")
                        for j, result in enumerate(results):
                            print(f"   {j+1}. {result.page_content[:50]}...")
                    except Exception as search_error:
                        print(f"❌ خطأ في البحث: {search_error}")
                else:
                    print(f"⚠️ Chroma فارغ!")
                    
            except Exception as chroma_error:
                print(f"❌ خطأ في فحص Chroma: {chroma_error}")
            
            print(f"\n🎉 تم إنجاز معالجة المواد مع Chroma!")
            
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_chroma())
