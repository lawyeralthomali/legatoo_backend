"""
فحص قاعدة البيانات لمعرفة عدد المواد المحفوظة
"""

import asyncio
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import LawArticle, LawSource, KnowledgeChunk
from sqlalchemy import select

async def check_database():
    """فحص محتويات قاعدة البيانات"""
    
    print("🔍 فحص قاعدة البيانات...")
    
    async with AsyncSessionLocal() as db:
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
        
        # عرض أول 10 مواد
        if articles:
            print(f"\n📋 أول 10 مواد:")
            for i, article in enumerate(articles[:10]):
                print(f"   {i+1}. {article.article_number}: {article.content[:50]}...")
        
        # عرض أول 10 chunks
        if chunks:
            print(f"\n📦 أول 10 chunks:")
            for i, chunk in enumerate(chunks[:10]):
                print(f"   {i+1}. Chunk {chunk.chunk_index}: {chunk.content[:50]}...")

if __name__ == "__main__":
    asyncio.run(check_database())
