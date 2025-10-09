"""
Fix Chunk Content - Include Article Title in Chunk Content
=====================================================

Problem: Chunks only contain article content, not the article title.
This causes poor search results because important keywords are in the title.

Solution: Update all chunks to include "Article Title + Content"
"""
import sys
import asyncio
import json
from sqlalchemy import select, update, func

sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeChunk, LawArticle


async def fix_chunk_content():
    """Update all chunks to include article title + content"""
    
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("🔧 FIX: Including Article Title in Chunk Content")
        print("=" * 80)
        
        # 1. Get all chunks with article_id
        result = await db.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.article_id.isnot(None))
        )
        chunks = result.scalars().all()
        
        print(f"\n📊 Found {len(chunks)} chunks linked to articles")
        
        if len(chunks) == 0:
            print("❌ No chunks found! Something is wrong.")
            return
        
        # 2. Update each chunk
        updated = 0
        skipped = 0
        
        for i, chunk in enumerate(chunks, 1):
            if i % 100 == 0:
                print(f"⚙️  Processing: {i}/{len(chunks)}...")
            
            # Get the article
            result2 = await db.execute(
                select(LawArticle).where(LawArticle.id == chunk.article_id)
            )
            article = result2.scalar_one_or_none()
            
            if not article:
                skipped += 1
                continue
            
            # Check if title is already in content
            if article.title and article.title not in chunk.content:
                # Create new content: Title + Content
                new_content = f"**{article.title}**\n\n{chunk.content}"
                
                # Update chunk
                chunk.content = new_content
                
                # Clear embedding (will be regenerated)
                chunk.embedding_vector = None
                
                updated += 1
                
                if updated <= 3:
                    print(f"\n✅ Updated Chunk {chunk.id} (Article {article.article_number}):")
                    print(f"   Title: {article.title}")
                    print(f"   New content: {new_content[:150]}...")
            else:
                skipped += 1
        
        # 3. Commit changes
        print(f"\n💾 Committing changes...")
        await db.commit()
        
        print(f"\n{'='*80}")
        print(f"✅ COMPLETED!")
        print(f"{'='*80}")
        print(f"📊 Updated: {updated} chunks")
        print(f"⏭️  Skipped: {skipped} chunks (already have title or no article)")
        print(f"\n⚠️  NEXT STEP: Re-generate embeddings for updated chunks")
        print(f"   Run: py scripts/regenerate_embeddings.py")


async def test_fix():
    """Test the fix with stamp forgery articles"""
    
    async with AsyncSessionLocal() as db:
        print("\n" + "=" * 80)
        print("🧪 Testing Fix - Stamp Forgery Articles")
        print("=" * 80)
        
        # Get chunks 6 and 7
        result = await db.execute(
            select(KnowledgeChunk, LawArticle)
            .join(LawArticle)
            .where(KnowledgeChunk.id.in_([6, 7]))
        )
        rows = result.all()
        
        for chunk, article in rows:
            print(f"\n📄 Chunk {chunk.id} - Article {article.article_number}")
            print(f"   Title: {article.title}")
            print(f"   Updated content: {chunk.content[:200]}...")
            print(f"   ✅ Title in content? {article.title in chunk.content}")


if __name__ == "__main__":
    print("🚀 Starting Chunk Content Fix...")
    print("=" * 80)
    asyncio.run(fix_chunk_content())
    asyncio.run(test_fix())

