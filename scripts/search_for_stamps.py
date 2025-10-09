"""Search for chunks containing 'طابع' (stamp)."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from sqlalchemy import select, or_
from app.models.legal_knowledge import KnowledgeChunk, LawArticle, LawSource

async def search_stamps():
    async with AsyncSessionLocal() as db:
        # Search for chunks containing 'طابع'
        chunks = await db.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.content.like('%طابع%'))
        )
        chunks = chunks.scalars().all()
        
        print("="*80)
        print(f"🔍 SEARCHING FOR 'طابع' (STAMP)")
        print("="*80)
        print(f"Found {len(chunks)} chunks containing 'طابع'\n")
        
        if len(chunks) == 0:
            print("❌ NO CHUNKS FOUND containing 'طابع'!")
            print("\n📊 This means:")
            print("   1. The uploaded laws don't contain articles about stamp forgery")
            print("   2. Or the specific law containing stamps wasn't uploaded")
            print("\n💡 SOLUTION:")
            print("   - Check which laws were uploaded (15 files)")
            print("   - Look for the law that contains stamp forgery articles")
            print("   - That law might be in the 19 failed JSON files")
        else:
            for chunk in chunks[:10]:  # Show first 10
                # Get article
                if chunk.article_id:
                    article = await db.scalar(
                        select(LawArticle).where(LawArticle.id == chunk.article_id)
                    )
                    if article:
                        # Get law source
                        law = await db.scalar(
                            select(LawSource).where(LawSource.id == article.law_source_id)
                        )
                        print(f"\n📄 Chunk {chunk.id}:")
                        print(f"   Law: {law.name if law else 'Unknown'}")
                        print(f"   Article: {article.article_number} - {article.title}")
                        print(f"   Content: {chunk.content[:150]}...")
                        print(f"   Has embedding: {chunk.embedding_vector is not None}")

if __name__ == "__main__":
    asyncio.run(search_stamps())

