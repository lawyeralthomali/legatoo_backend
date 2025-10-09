"""Check if chunk content includes article titles."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.legal_knowledge import KnowledgeChunk, LawArticle

async def check_chunk_format():
    async with AsyncSessionLocal() as db:
        # Get some sample chunks
        chunks = await db.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.article_id.isnot(None))
            .limit(5)
        )
        chunks = chunks.scalars().all()
        
        print("="*80)
        print("📋 CHUNK CONTENT FORMAT CHECK")
        print("="*80)
        
        correct_format = 0
        wrong_format = 0
        
        for chunk in chunks:
            # Get the article
            article = await db.scalar(
                select(LawArticle).where(LawArticle.id == chunk.article_id)
            )
            
            if article:
                has_title = article.title and chunk.content.startswith(f"**{article.title}**")
                
                print(f"\n📄 Chunk {chunk.id} (Article {article.article_number}):")
                print(f"   Article Title: {article.title[:50] if article.title else 'None'}...")
                print(f"   Chunk starts with: {chunk.content[:80]}...")
                print(f"   ✅ Has title: {has_title}")
                
                if has_title:
                    correct_format += 1
                else:
                    wrong_format += 1
        
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"✅ Chunks with title in content: {correct_format}/{len(chunks)}")
        print(f"❌ Chunks without title in content: {wrong_format}/{len(chunks)}")
        
        if wrong_format > 0:
            print("\n⚠️  ISSUE FOUND: Chunks don't include article titles!")
            print("📌 This was caused by uploading laws BEFORE the code fix.")
            print("🔧 SOLUTION: Re-upload the laws or run the chunk content fix script.")
        else:
            print("\n✅ All chunks have correct format with titles!")

if __name__ == "__main__":
    asyncio.run(check_chunk_format())

