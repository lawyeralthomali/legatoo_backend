"""Test arabic-st model."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import AsyncSessionLocal
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService

async def test():
    async with AsyncSessionLocal() as db:
        print("Testing arabic-st model...")
        svc = ArabicLegalEmbeddingService(db, model_name='arabic-st')
        svc.initialize_model()
        print("✅ arabic-st loaded!")
        
        # Test
        emb = svc.encode_text("تزوير طابع")
        print(f"Embedding dimension: {len(emb)}")

if __name__ == "__main__":
    asyncio.run(test())

