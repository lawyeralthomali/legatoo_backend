"""
Batch Embedding Generator - سكريبت المعالجة الجماعية للـ embeddings

This script processes all documents and chunks in the database to generate embeddings.
Can be run as a standalone script or scheduled as a background job.

Usage:
    python scripts/generate_embeddings_batch.py [options]

Options:
    --all              Process all documents
    --pending          Process only chunks without embeddings
    --document-id ID   Process specific document
    --resume           Resume failed processing
    --model MODEL      Model to use (default, large, small)
    --batch-size N     Batch size for processing
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_, or_, func

from app.models.legal_knowledge import KnowledgeDocument, KnowledgeChunk
from app.services.embedding_service import EmbeddingService
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging with UTF-8 encoding for Windows
import io
stdout_handler = logging.StreamHandler(sys.stdout)
# Try to set UTF-8 encoding for Windows console
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    # Python < 3.7 or already configured
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        stdout_handler,
        logging.FileHandler('logs/embedding_batch.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class BatchEmbeddingGenerator:
    """
    معالج جماعي لتوليد الـ embeddings للبيانات الحالية.
    
    Features:
    - Process all documents in the system
    - Process only pending chunks (without embeddings)
    - Resume failed processing
    - Progress tracking and reporting
    - Error handling and retry logic
    """
    
    def __init__(
        self,
        db: AsyncSession,
        model_name: str = 'default',
        batch_size: int = 32,
        retry_attempts: int = 3
    ):
        """
        Initialize batch generator.
        
        Args:
            db: Async database session
            model_name: Model to use for embeddings
            batch_size: Number of chunks to process in each batch
            retry_attempts: Number of retry attempts for failed chunks
        """
        self.db = db
        self.model_name = model_name
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.embedding_service = EmbeddingService(db, model_name=model_name)
        
        # Statistics
        self.stats = {
            "total_documents": 0,
            "processed_documents": 0,
            "failed_documents": 0,
            "total_chunks": 0,
            "processed_chunks": 0,
            "failed_chunks": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def process_all_documents(self) -> Dict[str, Any]:
        """
        يعالج جميع الـ documents في النظام.
        
        Returns:
            Dict with processing statistics
        """
        try:
            logger.info("=" * 80)
            logger.info("🚀 Starting FULL batch embedding generation")
            logger.info("=" * 80)
            
            self.stats["start_time"] = datetime.utcnow()
            
            # Get all documents
            result = await self.db.execute(select(KnowledgeDocument))
            documents = result.scalars().all()
            
            self.stats["total_documents"] = len(documents)
            logger.info(f"📄 Found {len(documents)} documents to process")
            
            # Process each document
            for i, document in enumerate(documents, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"📄 Processing document {i}/{len(documents)}: {document.title}")
                logger.info(f"{'='*60}")
                
                try:
                    result = await self.embedding_service.generate_document_embeddings(
                        document_id=document.id,
                        overwrite=False  # Don't overwrite existing embeddings
                    )
                    
                    if result.get("success", False):
                        self.stats["processed_documents"] += 1
                        self.stats["processed_chunks"] += result.get("processed_chunks", 0)
                        self.stats["failed_chunks"] += result.get("failed_chunks", 0)
                        logger.info(f"✅ Document {document.id} processed successfully")
                    else:
                        self.stats["failed_documents"] += 1
                        logger.error(f"❌ Failed to process document {document.id}: {result.get('error')}")
                    
                except Exception as e:
                    self.stats["failed_documents"] += 1
                    logger.error(f"❌ Exception processing document {document.id}: {str(e)}")
                    continue
            
            self.stats["end_time"] = datetime.utcnow()
            
            # Print final report
            self._print_report()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Fatal error in batch processing: {str(e)}")
            raise
    
    async def process_pending_chunks(self) -> Dict[str, Any]:
        """
        يعالج فقط الـ chunks التي لا تحتوي على embeddings.
        
        Returns:
            Dict with processing statistics
        """
        try:
            logger.info("=" * 80)
            logger.info("🚀 Starting PENDING chunks embedding generation")
            logger.info("=" * 80)
            
            self.stats["start_time"] = datetime.utcnow()
            
            # Get all chunks without embeddings
            query = select(KnowledgeChunk).where(
                or_(
                    KnowledgeChunk.embedding_vector.is_(None),
                    KnowledgeChunk.embedding_vector == ''
                )
            )
            
            result = await self.db.execute(query)
            pending_chunks = result.scalars().all()
            
            self.stats["total_chunks"] = len(pending_chunks)
            logger.info(f"📦 Found {len(pending_chunks)} pending chunks")
            
            if not pending_chunks:
                logger.info("✅ No pending chunks to process")
                return self.stats
            
            # Group chunks by document for better organization
            chunks_by_document: Dict[int, List[KnowledgeChunk]] = {}
            for chunk in pending_chunks:
                if chunk.document_id not in chunks_by_document:
                    chunks_by_document[chunk.document_id] = []
                chunks_by_document[chunk.document_id].append(chunk)
            
            logger.info(f"📄 Chunks distributed across {len(chunks_by_document)} documents")
            
            # Process each document's chunks
            for doc_id, chunks in chunks_by_document.items():
                logger.info(f"\n{'='*60}")
                logger.info(f"📄 Processing document {doc_id}: {len(chunks)} chunks")
                logger.info(f"{'='*60}")
                
                chunk_ids = [chunk.id for chunk in chunks]
                
                try:
                    result = await self.embedding_service.generate_batch_embeddings(
                        chunk_ids=chunk_ids,
                        overwrite=False
                    )
                    
                    if result.get("success", False):
                        self.stats["processed_chunks"] += result.get("processed_chunks", 0)
                        self.stats["failed_chunks"] += result.get("failed_chunks", 0)
                        logger.info(f"✅ Document {doc_id} chunks processed")
                    else:
                        self.stats["failed_chunks"] += len(chunk_ids)
                        logger.error(f"❌ Failed to process document {doc_id} chunks: {result.get('error')}")
                    
                except Exception as e:
                    self.stats["failed_chunks"] += len(chunk_ids)
                    logger.error(f"❌ Exception processing document {doc_id} chunks: {str(e)}")
                    continue
            
            self.stats["end_time"] = datetime.utcnow()
            
            # Print final report
            self._print_report()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Fatal error in pending chunks processing: {str(e)}")
            raise
    
    async def process_document(self, document_id: int) -> Dict[str, Any]:
        """
        يعالج document محدد فقط.
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            Dict with processing statistics
        """
        try:
            logger.info("=" * 80)
            logger.info(f"🚀 Starting embedding generation for document {document_id}")
            logger.info("=" * 80)
            
            self.stats["start_time"] = datetime.utcnow()
            self.stats["total_documents"] = 1
            
            # Process the document
            result = await self.embedding_service.generate_document_embeddings(
                document_id=document_id,
                overwrite=False
            )
            
            if result.get("success", False):
                self.stats["processed_documents"] = 1
                self.stats["total_chunks"] = result.get("total_chunks", 0)
                self.stats["processed_chunks"] = result.get("processed_chunks", 0)
                self.stats["failed_chunks"] = result.get("failed_chunks", 0)
                logger.info(f"✅ Document {document_id} processed successfully")
            else:
                self.stats["failed_documents"] = 1
                logger.error(f"❌ Failed to process document {document_id}: {result.get('error')}")
            
            self.stats["end_time"] = datetime.utcnow()
            
            # Print final report
            self._print_report()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Fatal error processing document {document_id}: {str(e)}")
            raise
    
    async def resume_failed_processing(self) -> Dict[str, Any]:
        """
        يستأنف المعالجة الفاشلة.
        
        Attempts to process chunks that failed in previous runs.
        Uses retry logic with exponential backoff.
        
        Returns:
            Dict with processing statistics
        """
        logger.info("=" * 80)
        logger.info("🔄 Resuming failed processing (same as pending for now)")
        logger.info("=" * 80)
        
        # For now, this is the same as processing pending chunks
        # In the future, we could track failed chunks separately
        return await self.process_pending_chunks()
    
    def _print_report(self) -> None:
        """Print final processing report."""
        logger.info("\n" + "=" * 80)
        logger.info("📊 BATCH PROCESSING REPORT")
        logger.info("=" * 80)
        
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            logger.info(f"⏱️  Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        logger.info(f"📄 Documents:")
        logger.info(f"   Total: {self.stats['total_documents']}")
        logger.info(f"   Processed: {self.stats['processed_documents']}")
        logger.info(f"   Failed: {self.stats['failed_documents']}")
        
        logger.info(f"\n📦 Chunks:")
        logger.info(f"   Total: {self.stats['total_chunks']}")
        logger.info(f"   Processed: {self.stats['processed_chunks']}")
        logger.info(f"   Failed: {self.stats['failed_chunks']}")
        
        if self.stats['total_chunks'] > 0:
            success_rate = (self.stats['processed_chunks'] / self.stats['total_chunks']) * 100
            logger.info(f"\n✅ Success Rate: {success_rate:.2f}%")
        
        logger.info("=" * 80 + "\n")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        يعرض حالة النظام قبل المعالجة.
        
        Returns:
            Dict with system status
        """
        try:
            # Total chunks
            total_result = await self.db.execute(select(func.count(KnowledgeChunk.id)))
            total_chunks = total_result.scalar() or 0
            
            # Chunks with embeddings
            with_embeddings_result = await self.db.execute(
                select(func.count(KnowledgeChunk.id)).where(
                    and_(
                        KnowledgeChunk.embedding_vector.isnot(None),
                        KnowledgeChunk.embedding_vector != ''
                    )
                )
            )
            with_embeddings = with_embeddings_result.scalar() or 0
            
            # Chunks without embeddings
            without_embeddings = total_chunks - with_embeddings
            
            # Completion percentage
            completion = (with_embeddings / total_chunks * 100) if total_chunks > 0 else 0
            
            return {
                "total_chunks": total_chunks,
                "chunks_with_embeddings": with_embeddings,
                "chunks_without_embeddings": without_embeddings,
                "completion_percentage": round(completion, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get system status: {str(e)}")
            return {}


async def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Batch embedding generation for legal knowledge chunks"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all documents'
    )
    parser.add_argument(
        '--pending',
        action='store_true',
        help='Process only chunks without embeddings'
    )
    parser.add_argument(
        '--document-id',
        type=int,
        help='Process specific document by ID'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume failed processing'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='default',
        choices=['default', 'large', 'small'],
        help='Embedding model to use'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for processing'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show system status and exit'
    )
    
    args = parser.parse_args()
    
    # Get DATABASE_URL from environment
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    
    # Create async engine and session
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True
    )
    
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Initialize batch generator
        generator = BatchEmbeddingGenerator(
            db=session,
            model_name=args.model,
            batch_size=args.batch_size
        )
        
        # Show status if requested
        if args.status:
            status = await generator.get_system_status()
            logger.info("=" * 80)
            logger.info("📊 SYSTEM STATUS")
            logger.info("=" * 80)
            logger.info(f"📦 Total chunks: {status.get('total_chunks', 0)}")
            logger.info(f"✅ With embeddings: {status.get('chunks_with_embeddings', 0)}")
            logger.info(f"⏳ Without embeddings: {status.get('chunks_without_embeddings', 0)}")
            logger.info(f"📈 Completion: {status.get('completion_percentage', 0):.2f}%")
            logger.info("=" * 80)
            return
        
        # Determine which processing mode to use
        if args.document_id:
            logger.info(f"📄 Processing document {args.document_id}")
            await generator.process_document(args.document_id)
        elif args.pending:
            logger.info("⏳ Processing pending chunks only")
            await generator.process_pending_chunks()
        elif args.resume:
            logger.info("🔄 Resuming failed processing")
            await generator.resume_failed_processing()
        elif args.all:
            logger.info("🌍 Processing all documents")
            await generator.process_all_documents()
        else:
            # Default: process pending chunks
            logger.info("⏳ Processing pending chunks (default mode)")
            await generator.process_pending_chunks()
    
    logger.info("✅ Batch processing completed")


if __name__ == "__main__":
    asyncio.run(main())
