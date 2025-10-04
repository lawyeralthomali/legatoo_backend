#!/usr/bin/env python3
"""
Quick Legal Documents Cleanup Script

Simple script to delete all legal documents and chunks from the database.
This is a minimal version for quick cleanup operations.

Usage:
    python cleanup_legal_docs.py
"""

import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import delete, text
from app.db.database import AsyncSessionLocal
from app.models.legal_document2 import LegalDocument, LegalDocumentChunk


async def quick_cleanup():
    """Quick cleanup - delete all documents and chunks."""
    print("🗑️  Quick Legal Documents Cleanup")
    print("-" * 40)
    
    async with AsyncSessionLocal() as db:
        try:
            # Get counts first
            doc_count_query = text("SELECT COUNT(*) FROM legal_documents")
            chunk_count_query = text("SELECT COUNT(*) FROM legal_document_chunks")
            
            doc_count = await db.execute(doc_count_query)
            chunk_count = await db.execute(chunk_count_query)
            
            docs = doc_count.scalar()
            chunks = chunk_count.scalar()
            
            print(f"Found: {docs} documents, {chunks} chunks")
            
            if docs == 0 and chunks == 0:
                print("✅ Database is already clean!")
                return
            
            # Delete chunks first (due to foreign key constraint)
            if chunks > 0:
                await db.execute(delete(LegalDocumentChunk))
                print(f"✅ Deleted {chunks} chunks")
            
            # Delete documents
            if docs > 0:
                await db.execute(delete(LegalDocument))
                print(f"✅ Deleted {docs} documents")
            
            # Commit changes
            await db.commit()
            print("🎉 Database cleanup completed!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    try:
        asyncio.run(quick_cleanup())
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
    except Exception as e:
        print(f"❌ Failed: {e}")
