"""
Migration Script: Upgrade to Arabic Legal Model

This script migrates from the old generic multilingual model to the new
Arabic-specialized legal model.

Steps:
1. Backup existing embeddings
2. Initialize new Arabic model
3. Re-generate embeddings for all chunks
4. Build FAISS index
5. Validate results
6. Update configuration

Usage:
    python scripts/migrate_to_arabic_model.py --model arabert --use-faiss
"""

import asyncio
import argparse
import logging
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import sessionmaker

from app.models.legal_knowledge import KnowledgeChunk
from app.services.arabic_legal_embedding_service import ArabicLegalEmbeddingService
from app.db.database import DATABASE_URL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages the migration to Arabic legal model."""
    
    def __init__(
        self,
        database_url: str,
        model_name: str = 'paraphrase-multilingual',
        use_faiss: bool = True,
        batch_size: int = 100
    ):
        """
        Initialize migration manager.
        
        Args:
            database_url: Database connection URL
            model_name: Model to use ('paraphrase-multilingual', 'labse')
            use_faiss: Whether to build FAISS index
            batch_size: Batch size for processing
        """
        self.database_url = database_url
        self.model_name = model_name
        self.use_faiss = use_faiss
        self.batch_size = batch_size
        
        self.engine = None
        self.SessionLocal = None
        self.backup_dir = Path("migration_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info("🚀 Migration Manager initialized")
        logger.info(f"   Model: {model_name}")
        logger.info(f"   FAISS: {use_faiss}")
        logger.info(f"   Batch size: {batch_size}")
    
    async def setup_database(self) -> None:
        """Setup database connection."""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True
        )
        
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("✅ Database connection established")
    
    async def backup_embeddings(self) -> str:
        """
        Backup existing embeddings.
        
        Returns:
            Path to backup file
        """
        logger.info("📦 Backing up existing embeddings...")
        
        async with self.SessionLocal() as db:
            # Get all chunks with embeddings
            query = select(KnowledgeChunk).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != ''
                )
            )
            
            result = await db.execute(query)
            chunks = result.scalars().all()
            
            if not chunks:
                logger.warning("⚠️  No embeddings found to backup")
                return None
            
            logger.info(f"   Found {len(chunks)} chunks with embeddings")
            
            # Create backup data
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_chunks': len(chunks),
                'embeddings': []
            }
            
            for chunk in chunks:
                backup_data['embeddings'].append({
                    'chunk_id': chunk.id,
                    'embedding_vector': chunk.embedding_vector,
                    'created_at': chunk.created_at.isoformat() if chunk.created_at else None
                })
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f"embeddings_backup_{timestamp}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Backup saved: {backup_file}")
            logger.info(f"   Size: {backup_file.stat().st_size / 1024 / 1024:.2f} MB")
            
            return str(backup_file)
    
    async def get_chunks_to_process(self, overwrite: bool = True) -> List[int]:
        """
        Get list of chunk IDs to process.
        
        Args:
            overwrite: If True, reprocess all chunks; if False, only missing
            
        Returns:
            List of chunk IDs
        """
        async with self.SessionLocal() as db:
            if overwrite:
                # Get all chunks
                query = select(KnowledgeChunk.id)
            else:
                # Get only chunks without embeddings
                query = select(KnowledgeChunk.id).where(
                    or_(
                        KnowledgeChunk.embedding_vector.is_(None),
                        KnowledgeChunk.embedding_vector == ''
                    )
                )
            
            result = await db.execute(query)
            chunk_ids = [row[0] for row in result.all()]
            
            return chunk_ids
    
    async def regenerate_embeddings(self, chunk_ids: List[int]) -> Dict[str, Any]:
        """
        Re-generate embeddings for chunks.
        
        Args:
            chunk_ids: List of chunk IDs to process
            
        Returns:
            Processing statistics
        """
        logger.info(f"🔄 Re-generating embeddings for {len(chunk_ids)} chunks...")
        
        async with self.SessionLocal() as db:
            # Initialize embedding service
            service = ArabicLegalEmbeddingService(
                db=db,
                model_name=self.model_name,
                use_faiss=self.use_faiss
            )
            
            # Load model
            logger.info("📥 Loading Arabic model...")
            service.initialize_model()
            logger.info("✅ Model loaded")
            
            # Process in batches
            total_processed = 0
            total_failed = 0
            start_time = datetime.utcnow()
            
            for i in range(0, len(chunk_ids), self.batch_size):
                batch = chunk_ids[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(chunk_ids) + self.batch_size - 1) // self.batch_size
                
                logger.info(f"⚙️  Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)")
                
                result = await service.generate_batch_embeddings(
                    chunk_ids=batch,
                    overwrite=True
                )
                
                total_processed += result.get('processed_chunks', 0)
                total_failed += result.get('failed_chunks', 0)
                
                logger.info(f"   ✓ Processed: {result.get('processed_chunks', 0)}")
                logger.info(f"   ✗ Failed: {result.get('failed_chunks', 0)}")
                logger.info(f"   ⚡ Speed: {result.get('speed', 'N/A')}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Embedding generation complete!")
            logger.info(f"   Total processed: {total_processed}")
            logger.info(f"   Total failed: {total_failed}")
            logger.info(f"   Processing time: {processing_time:.2f}s")
            logger.info(f"   Average speed: {total_processed / processing_time:.1f} chunks/sec")
            logger.info(f"{'='*60}\n")
            
            return {
                'success': True,
                'total_chunks': len(chunk_ids),
                'processed': total_processed,
                'failed': total_failed,
                'processing_time': processing_time,
                'speed': total_processed / processing_time
            }
    
    async def build_faiss_index(self) -> Dict[str, Any]:
        """
        Build FAISS index for fast search.
        
        Returns:
            Index statistics
        """
        if not self.use_faiss:
            logger.info("⏭️  Skipping FAISS index (disabled)")
            return {'success': False, 'reason': 'FAISS disabled'}
        
        logger.info("🔨 Building FAISS index...")
        
        async with self.SessionLocal() as db:
            service = ArabicLegalEmbeddingService(
                db=db,
                model_name=self.model_name,
                use_faiss=True
            )
            
            service.initialize_model()
            result = await service.build_faiss_index()
            
            if result.get('success'):
                logger.info(f"✅ FAISS index built successfully!")
                logger.info(f"   Total vectors: {result.get('total_vectors')}")
                logger.info(f"   Dimension: {result.get('dimension')}")
            else:
                logger.error(f"❌ FAISS index build failed: {result.get('error')}")
            
            return result
    
    async def validate_migration(self) -> Dict[str, Any]:
        """
        Validate the migration by testing search.
        
        Returns:
            Validation results
        """
        logger.info("🧪 Validating migration...")
        
        test_queries = [
            "فسخ عقد العمل",
            "حقوق العامل",
            "التعويض"
        ]
        
        async with self.SessionLocal() as db:
            from app.services.arabic_legal_search_service import ArabicLegalSearchService
            
            search = ArabicLegalSearchService(
                db=db,
                model_name=self.model_name,
                use_faiss=self.use_faiss
            )
            
            await search.initialize()
            
            results = []
            for query in test_queries:
                logger.info(f"   Testing query: '{query}'")
                
                try:
                    search_results = await search.find_similar_laws(
                        query=query,
                        top_k=5,
                        threshold=0.6
                    )
                    
                    logger.info(f"      ✓ Found {len(search_results)} results")
                    
                    results.append({
                        'query': query,
                        'results_count': len(search_results),
                        'success': True
                    })
                    
                except Exception as e:
                    logger.error(f"      ✗ Error: {str(e)}")
                    results.append({
                        'query': query,
                        'success': False,
                        'error': str(e)
                    })
            
            all_successful = all(r['success'] for r in results)
            
            if all_successful:
                logger.info("✅ Validation successful!")
            else:
                logger.warning("⚠️  Validation completed with errors")
            
            return {
                'success': all_successful,
                'test_results': results
            }
    
    async def run_migration(self, skip_backup: bool = False) -> None:
        """
        Run the complete migration process.
        
        Args:
            skip_backup: Skip backup step (not recommended)
        """
        logger.info("\n" + "="*60)
        logger.info("🚀 STARTING MIGRATION TO ARABIC LEGAL MODEL")
        logger.info("="*60 + "\n")
        
        try:
            # Step 1: Setup database
            await self.setup_database()
            
            # Step 2: Backup
            if not skip_backup:
                backup_file = await self.backup_embeddings()
            else:
                logger.warning("⚠️  Skipping backup (not recommended)")
                backup_file = None
            
            # Step 3: Get chunks to process
            logger.info("\n📊 Analyzing chunks...")
            chunk_ids = await self.get_chunks_to_process(overwrite=True)
            logger.info(f"   Found {len(chunk_ids)} chunks to process")
            
            if not chunk_ids:
                logger.warning("⚠️  No chunks found to process")
                return
            
            # Step 4: Re-generate embeddings
            embedding_result = await self.regenerate_embeddings(chunk_ids)
            
            # Step 5: Build FAISS index
            if self.use_faiss:
                faiss_result = await self.build_faiss_index()
            else:
                faiss_result = None
            
            # Step 6: Validate
            validation_result = await self.validate_migration()
            
            # Summary
            logger.info("\n" + "="*60)
            logger.info("📊 MIGRATION SUMMARY")
            logger.info("="*60)
            logger.info(f"Backup file: {backup_file or 'Skipped'}")
            logger.info(f"Chunks processed: {embedding_result['processed']}/{embedding_result['total_chunks']}")
            logger.info(f"Processing time: {embedding_result['processing_time']:.2f}s")
            logger.info(f"Speed: {embedding_result['speed']:.1f} chunks/sec")
            if faiss_result:
                logger.info(f"FAISS vectors: {faiss_result.get('total_vectors', 'N/A')}")
            logger.info(f"Validation: {'✅ Passed' if validation_result['success'] else '❌ Failed'}")
            logger.info("="*60 + "\n")
            
            if validation_result['success']:
                logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY!")
                logger.info("\n📝 Next steps:")
                logger.info("   1. Test the API endpoints")
                logger.info("   2. Monitor performance in production")
                logger.info("   3. Remove old model files if everything works")
            else:
                logger.warning("⚠️  MIGRATION COMPLETED WITH WARNINGS")
                logger.warning("   Please review the validation errors above")
            
        except Exception as e:
            logger.error(f"\n❌ MIGRATION FAILED: {str(e)}")
            raise
        finally:
            if self.engine:
                await self.engine.dispose()


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Migrate to Arabic Legal Model')
    parser.add_argument(
        '--model',
        type=str,
        default='paraphrase-multilingual',
        choices=['paraphrase-multilingual', 'labse', 'arabert-raw'],
        help='Model to use (default: paraphrase-multilingual)'
    )
    parser.add_argument(
        '--use-faiss',
        action='store_true',
        default=True,
        help='Build FAISS index for fast search'
    )
    parser.add_argument(
        '--no-faiss',
        action='store_true',
        help='Disable FAISS indexing'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing (default: 100)'
    )
    parser.add_argument(
        '--skip-backup',
        action='store_true',
        help='Skip backup step (not recommended)'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        help='Database URL (default: from config)'
    )
    
    args = parser.parse_args()
    
    # Get database URL
    if args.database_url:
        database_url = args.database_url
    else:
        # Use the DATABASE_URL from app.db.database
        database_url = DATABASE_URL
        logger.info(f"📊 Using database: {database_url}")
    
    # Create migration manager
    manager = MigrationManager(
        database_url=database_url,
        model_name=args.model,
        use_faiss=not args.no_faiss,
        batch_size=args.batch_size
    )
    
    # Run migration
    await manager.run_migration(skip_backup=args.skip_backup)


if __name__ == '__main__':
    asyncio.run(main())

