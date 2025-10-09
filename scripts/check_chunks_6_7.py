"""Quick check for chunks 6 and 7"""
import sys
import asyncio

sys.path.insert(0, '.')
from app.db.database import AsyncSessionLocal
from app.models.legal_knowledge import KnowledgeChunk
from sqlalchemy import select


async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.id.in_([6, 7]))
        )
        chunks = result.scalars().all()
        
        for c in chunks:
            print(f"Chunk {c.id}:")
            print(f"  Content: {c.content[:200]}")
            print(f"  Has embedding: {c.embedding_vector is not None}")
            print()


asyncio.run(check())

