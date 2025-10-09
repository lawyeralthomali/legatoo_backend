"""
Check chunks related to stamp forgery in the database
"""
import sys
import asyncio
from sqlalchemy import select, text, func

sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeChunk, LawArticle


async def check_stamp_chunks():
    """Check if stamp forgery articles are properly chunked in DB"""
    
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("🔍 Checking Chunks for Stamp Forgery (تزوير الطوابع)")
        print("=" * 80)
        
        # 1. Check chunks containing 'طابع' (stamp)
        result = await db.execute(
            text("""
                SELECT id, content, tokens_count, article_id 
                FROM knowledge_chunks 
                WHERE content LIKE '%طابع%' 
                LIMIT 10
            """)
        )
        rows = result.all()
        
        print(f"\n📊 Chunks containing 'طابع' (stamp): {len(rows)}")
        print("-" * 80)
        
        for r in rows:
            chunk_id, content, tokens, article_id = r
            print(f"\n🔹 Chunk ID: {chunk_id}")
            print(f"   Article ID: {article_id}")
            print(f"   Tokens: {tokens}")
            print(f"   Content: {content[:200]}...")
        
        # 2. Check articles with numbers 'السادسة' or 'السابعة' (6th and 7th)
        print("\n" + "=" * 80)
        print("📚 Articles 6 & 7 (Stamp Forgery Articles)")
        print("=" * 80)
        
        result = await db.execute(
            select(LawArticle.id, LawArticle.article_number, LawArticle.title, LawArticle.content)
            .where(LawArticle.article_number.in_(['السادسة', 'السابعة']))
        )
        articles = result.all()
        
        for article in articles:
            art_id, art_num, title, content = article
            print(f"\n📄 Article {art_num}: {title}")
            print(f"   ID: {art_id}")
            print(f"   Content preview: {content[:300]}...")
            
            # Check chunks for this article
            result2 = await db.execute(
                select(func.count(KnowledgeChunk.id))
                .where(KnowledgeChunk.article_id == art_id)
            )
            chunk_count = result2.scalar()
            print(f"   ✅ Chunks created: {chunk_count}")
            
            # Get actual chunks
            result3 = await db.execute(
                select(KnowledgeChunk.id, KnowledgeChunk.content, KnowledgeChunk.tokens_count)
                .where(KnowledgeChunk.article_id == art_id)
                .limit(5)
            )
            chunks = result3.all()
            
            for chunk in chunks:
                chunk_id, chunk_content, tokens = chunk
                print(f"      • Chunk {chunk_id}: {tokens} tokens - {chunk_content[:100]}...")
        
        # 3. Check total chunks in system
        print("\n" + "=" * 80)
        print("📈 Overall System Statistics")
        print("=" * 80)
        
        result = await db.execute(
            select(func.count(KnowledgeChunk.id))
        )
        total_chunks = result.scalar()
        
        result = await db.execute(
            select(func.count(KnowledgeChunk.id))
            .where(KnowledgeChunk.embedding_vector.isnot(None))
        )
        chunks_with_embeddings = result.scalar()
        
        print(f"📊 Total chunks: {total_chunks}")
        print(f"✅ Chunks with embeddings: {chunks_with_embeddings}")
        print(f"📉 Chunks without embeddings: {total_chunks - chunks_with_embeddings}")


if __name__ == "__main__":
    asyncio.run(check_stamp_chunks())

