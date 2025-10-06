#!/usr/bin/env python3
"""
Database Cleanup Script for Legal Assistant

This script removes all legal documents and their associated chunks from the database.
Optionally, it can also delete the physical files from the uploads directory.

Usage:
    python delete_all_documents.py                    # Delete from database only
    python delete_all_documents.py --delete-files    # Delete from DB + filesystem
    python delete_all_documents.py --dry-run          # Show what would be deleted
    python delete_all_documents.py --confirm-all      # Skip confirmation prompts
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db.database import AsyncSessionLocal
from app.models.legal_document2 import LegalDocument, LegalDocumentChunk


class DocumentCleanupService:
    """Service for deleting all legal documents and chunks."""
    
    def __init__(self):
        self.upload_base_dir = Path("uploads/legal_documents")
    
    async def get_document_stats(self, db: AsyncSession) -> dict:
        """Get statistics about documents and chunks in the database."""
        try:
            # Count documents
            doc_count_query = text("SELECT COUNT(*) as count FROM legal_documents")
            doc_result = await db.execute(doc_count_query)
            doc_count = doc_result.scalar()
            
            # Count chunks
            chunk_count_query = text("SELECT COUNT(*) as count FROM legal_document_chunks")
            chunk_result = await db.execute(chunk_count_query)
            chunk_count = chunk_result.scalar()
            
            # Get total file size on disk
            total_size = await self._calculate_total_file_size()
            
            return {
                "documents": doc_count or 0,
                "chunks": chunk_count or 0,
                "total_file_size_mb": round(total_size, 2)
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {"documents": 0, "chunks": 0, "total_file_size_mb": 0}
    
    async def _calculate_total_file_size(self) -> float:
        """Calculate total size of uploaded files in MB."""
        try:
            total_size = 0
            if self.upload_base_dir.exists():
                for file_path in self.upload_base_dir.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception:
            return 0
    
    async def delete_all_chunks(self, db: AsyncSession) -> int:
        """Delete all document chunks from database."""
        try:
            print("🗑️  Deleting all document chunks...")
            result = await db.execute(delete(LegalDocumentChunk))
            deleted_chunks = result.rowcount
            print(f"✅ Deleted {deleted_chunks} chunks")
            return deleted_chunks
        except Exception as e:
            print(f"❌ Error deleting chunks: {e}")
            return 0
    
    async def delete_all_documents(self, db: AsyncSession) -> int:
        """Delete all documents from database."""
        try:
            print("🗑️  Deleting all documents...")
            result = await db.execute(delete(LegalDocument))
            deleted_docs = result.rowcount
            print(f"✅ Deleted {deleted_docs} documents")
            return deleted_docs
        except Exception as e:
            print(f"❌ Error deleting documents: {e}")
            return 0
    
    async def delete_uploaded_files(self) -> tuple[int, float]:
        """Delete all uploaded files from filesystem."""
        try:
            if not self.upload_base_dir.exists():
                print("📁 Uploads directory doesn't exist - nothing to delete")
                return 0, 0.0
            
            deleted_files = 0
            total_size_deleted = 0
            
            print("🗑️  Deleting uploaded files...")
            for file_path in self.upload_base_dir.rglob("*"):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    file_path.unlink()  # Delete the file
                    deleted_files += 1
                    total_size_deleted += file_size
                    print(f"   📄 Deleted: {file_path.name}")
            
            # Remove empty directories
            for dir_path in self.upload_base_dir.rglob("*"):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
            
            size_mb = total_size_deleted / (1024 * 1024)
            print(f"✅ Deleted {deleted_files} files ({size_mb:.2f} MB)")
            return deleted_files, size_mb
            
        except Exception as e:
            print(f"❌ Error deleting files: {e}")
            return 0, 0.0
    
    async def cleanup_faiss_indexes(self) -> None:
        """Optional: Clean up FAISS indexes if they exist."""
        faiss_dir = Path("faiss_indexes")
        if faiss_dir.exists():
            try:
                print("🗑️  Cleaning up FAISS indexes...")
                for file_path in faiss_dir.rglob("*"):
                    if file_path.is_file():
                        file_path.unlink()
                        print(f"   🗂️  Deleted: {file_path.name}")
                
                # Remove empty directories
                for dir_path in faiss_dir.rglob("*"):
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                
                print("✅ FAISS indexes cleaned up")
            except Exception as e:
                print(f"⚠️  Error cleaning FAISS indexes: {e}")


async def main():
    """Main cleanup function."""
    parser = argparse.ArgumentParser(
        description="Delete all legal documents and chunks from database"
    )
    parser.add_argument(
        "--delete-files",
        action="store_true",
        help="Also delete uploaded files from filesystem"
    )
    parser.add_argument(
        "--delete-faiss",
        action="store_true", 
        help="Also delete FAISS vector indexes"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--confirm-all",
        action="store_true",
        help="Skip confirmation prompts (use with caution!)"
    )
    
    args = parser.parse_args()
    
    service = DocumentCleanupService()
    
    print("🔍 Legal Document Cleanup Tool")
    print("=" * 50)
    
    # Connect to database and get stats
    async with AsyncSessionLocal() as db:
        stats = await service.get_document_stats(db)
        
        print(f"📊 Current Database State:")
        print(f"   📄 Documents: {stats['documents']}")
        print(f"   🧩 Chunks: {stats['chunks']}")
        print(f"   💾 Files on disk: {stats['total_file_size_mb']:.2f} MB")
        print()
        
        if stats['documents'] == 0 and stats['chunks'] == 0:
            print("✅ Database is already clean - no documents or chunks found!")
            return
        
        if args.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            print(f"   Would delete: {stats['documents']} documents, {stats['chunks']} chunks")
            if args.delete_files:
                print(f"   Would delete files: {stats['total_file_size_mb']:.2f} MB")
            return
        
        # Confirmation prompts
        if not args.confirm_all:
            print("⚠️  WARNING: This will permanently delete:")
            print(f"   • {stats['documents']} documents from database")
            print(f"   • {stats['chunks']} chunks from database")
            if args.delete_files:
                print(f"   • All uploaded files ({stats['total_file_size_mb']:.2f} MB)")
            
            confirm = input("\n❓ Are you sure you want to proceed? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("❌ Operation cancelled")
                return
        
        # Perform cleanup
        print("\n🚀 Starting cleanup...")
        
        deleted_docs = 0
        deleted_chunks = 0
        deleted_files = 0
        deleted_size_mb = 0.0
        
        try:
            # Delete in correct order (chunks first due to foreign key constraints)
            deleted_chunks = await service.delete_all_chunks(db)
            deleted_docs = await service.delete_all_documents(db)
            
            # Commit database changes
            await db.commit()
            
            # Clean up files if requested
            if args.delete_files:
                print()
                files_deleted, size_deleted = await service.delete_uploaded_files()
                deleted_files = files_deleted
                deleted_size_mb = size_deleted
            
            # Clean up FAISS indexes if requested
            if args.delete_faiss:
                print()
                await service.cleanup_faiss_indexes()
            
            print("\n🎉 Cleanup completed successfully!")
            print("=" * 50)
            print("📊 Summary:")
            print(f"   ✅ Documents deleted: {deleted_docs}")
            print(f"   ✅ Chunks deleted: {deleted_chunks}")
            if args.delete_files:
                print(f"   ✅ Files deleted: {deleted_files}")
                print(f"   ✅ Storage freed: {deleted_size_mb:.2f} MB")
            
        except Exception as e:
            print(f"\n❌ ERROR during cleanup: {e}")
            await db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
