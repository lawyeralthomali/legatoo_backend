"""
تنظيف قاعدة البيانات
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

if __name__ == "__main__":
    asyncio.run(clean_database())
