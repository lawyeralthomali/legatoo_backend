"""Quick script to check chunks and embeddings status."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.models.legal_knowledge import KnowledgeChunk, LawArticle, LawSource

async def check_status():
    async with AsyncSessionLocal() as db:
        # Count total chunks
        total_chunks = await db.scalar(select(func.count(KnowledgeChunk.id)))
        
        # Count chunks with embeddings
        chunks_with_emb = await db.scalar(
            select(func.count(KnowledgeChunk.id)).where(
                KnowledgeChunk.embedding_vector.isnot(None)
            )
        )
        
        # Count law sources
        total_laws = await db.scalar(select(func.count(LawSource.id)))
        
        # Count articles
        total_articles = await db.scalar(select(func.count(LawArticle.id)))
        
        print("="*60)
        print("📊 DATABASE STATUS")
        print("="*60)
        print(f"📚 Total Law Sources: {total_laws}")
        print(f"📄 Total Articles: {total_articles}")
        print(f"🧩 Total Chunks: {total_chunks}")
        print(f"✅ Chunks with Embeddings: {chunks_with_emb}")
        print(f"❌ Chunks without Embeddings: {total_chunks - chunks_with_emb}")
        print("="*60)
        
        if chunks_with_emb == 0 and total_chunks > 0:
            print("⚠️  WARNING: No embeddings found! Run migrate_to_arabic_model.py")
        elif total_chunks == 0:
            print("⚠️  WARNING: No chunks found! Laws may not be processed yet.")
        elif chunks_with_emb == total_chunks:
            print("✅ SUCCESS: All chunks have embeddings!")
        else:
            print(f"⚠️  PARTIAL: {chunks_with_emb}/{total_chunks} chunks have embeddings")

if __name__ == "__main__":
    asyncio.run(check_status())

