"""
Complete Legal AI Service - Phase 3 & 4 Integration

This is the main orchestrator service that combines:
- Enhanced Document Processing (Phase 3)
- Enhanced Embedding Generation (Phase 4)
- FAISS Vector Search (Phase 4)

Complete workflow:
1. Upload document (PDF, DOCX, Image)
2. Extract and clean text
3. Split into chunks (300-500 words)
4. Generate embeddings
5. Index in FAISS
6. Enable semantic search

Ready for AI integration!
"""

import logging
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.legal_document2 import LegalDocument, LegalDocumentChunk, ProcessingStatusEnum
from ..repositories.legal_document_repository import LegalDocumentRepository
from .enhanced_document_processor import EnhancedDocumentProcessor
from .enhanced_embedding_service import EnhancedEmbeddingService
from .faiss_search_service import FAISSSearchService

logger = logging.getLogger(__name__)


class CompleteLegalAIService:
    """
    Complete Legal AI Service - Orchestrates entire workflow.
    
    Phase 3 & 4 Implementation:
    - Document upload and processing
    - Text extraction with OCR support
    - Intelligent chunking
    - Embedding generation
    - FAISS indexing
    - Semantic search
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the complete legal AI service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = LegalDocumentRepository(db)
        
        # Initialize sub-services
        self.doc_processor = EnhancedDocumentProcessor()
        self.embedding_service = EnhancedEmbeddingService()
        self.faiss_service = FAISSSearchService(
            embedding_dimension=self.embedding_service.embedding_dimension
        )
        
        # Configuration
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads/legal_documents"))
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Complete Legal AI Service initialized")

    # ==================== PHASE 3: DOCUMENT UPLOAD & PROCESSING ====================

    async def upload_and_process_document(
        self,
        file_path: str,
        original_filename: str,
        title: str,
        document_type: str,
        language: str,
        uploaded_by_id: Optional[int] = None,
        notes: Optional[str] = None,
        process_immediately: bool = True
    ) -> LegalDocument:
        """
        Complete workflow: Upload → Extract → Chunk → Embed → Index
        
        Phase 3 & 4 Implementation
        
        Args:
            file_path: Path to uploaded file
            original_filename: Original filename
            title: Document title
            document_type: Type of document
            language: Document language
            uploaded_by_id: User who uploaded
            notes: Additional notes
            process_immediately: Process now or queue
            
        Returns:
            Created LegalDocument instance
        """
        # Validate file format
        file_extension = Path(original_filename).suffix.lower()
        if not self.doc_processor.is_supported_format(file_extension):
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Create document record
        document = await self.repository.create_document(
            title=title,
            file_path=file_path,
            document_type=document_type,
            language=language,
            uploaded_by_id=uploaded_by_id,
            notes=notes
        )
        
        logger.info(f"✅ Document {document.id} uploaded: {title}")
        
        # Process document if requested
        if process_immediately:
            # Create a new task with its own database session
            asyncio.create_task(self._process_document_async(document.id))
        
        return document

    async def _process_document_async(self, document_id: int) -> bool:
        """
        Process document in background with its own database session.
        
        This method creates a new database session to avoid conflicts
        with the main request session.
        """
        from ..db.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            # Create a new service instance with the new session
            service = CompleteLegalAIService(db)
            return await service.process_document(document_id)

    async def process_document(self, document_id: int) -> bool:
        """
        Complete processing pipeline for a document.
        
        Pipeline:
        1. Extract text from file
        2. Clean and normalize text
        3. Split into chunks (300-500 words)
        4. Generate embeddings
        5. Add to FAISS index
        6. Save to database
        
        Args:
            document_id: ID of document to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update status
            from ..models.legal_document2 import ProcessingStatusEnum
            await self.repository.update_document(
                document_id,
                processing_status=ProcessingStatusEnum.PROCESSING
            )
            
            # Get document
            document = await self.repository.get_document_by_id(document_id)
            if not document:
                logger.error(f"Document {document_id} not found")
                return False
            
            logger.info(f"🚀 Starting processing for document {document_id}: {document.title}")
            
            # ========== PHASE 3: TEXT EXTRACTION ==========
            
            logger.info("Step 1/5: Extracting text...")
            file_extension = Path(document.file_path).suffix
            
            # Extract text with detailed error handling
            try:
                text_content = await self.doc_processor.extract_text_from_file(
                    document.file_path,
                    file_extension,
                    document.language
                )
            except Exception as extract_error:
                error_msg = f"Failed to extract text from file: {str(extract_error)}"
                logger.error(error_msg)
                await self.repository.update_document(
                    document_id,
                    processing_status=ProcessingStatusEnum.ERROR,
                    notes=f"Extraction failed: {str(extract_error)}"
                )
                raise ValueError(error_msg)
            
            # Validate extracted text
            if not text_content:
                error_msg = "No text could be extracted from the PDF"
                logger.error(f"Extraction returned empty text for document {document_id}")
                await self.repository.update_document(
                    document_id,
                    processing_status=ProcessingStatusEnum.ERROR,
                    notes="No text extracted - PDF may be image-based or empty"
                )
                raise ValueError(error_msg)
            
            text_length = len(text_content.strip())
            if text_length < 100:
                error_msg = f"Extracted text is too short ({text_length} characters). PDF may be corrupted, empty, or require OCR."
                logger.warning(error_msg)
                # Still allow processing if there's some text (changed from hard error)
                if text_length < 20:
                    await self.repository.update_document(
                        document_id,
                        processing_status=ProcessingStatusEnum.ERROR,
                        notes=f"Text too short: {text_length} chars"
                    )
                    raise ValueError(error_msg)
                else:
                    logger.warning(f"Proceeding with short text ({text_length} chars) for document {document_id}")
            
            logger.info(f"✅ Extracted {len(text_content)} characters (stripped: {text_length} chars)")
            
            # ========== SAVE EXTRACTED TEXT TO FILE ==========
            
            # Create extracted text directory
            extracted_text_dir = Path("uploads/extracted_text")
            extracted_text_dir.mkdir(parents=True, exist_ok=True)
            
            # Save raw extracted text
            raw_text_file = extracted_text_dir / f"document_{document_id}_raw.txt"
            with open(raw_text_file, 'w', encoding='utf-8') as f:
                f.write(f"=== RAW EXTRACTED TEXT FOR DOCUMENT {document_id} ===\n")
                f.write(f"Title: {document.title}\n")
                f.write(f"Language: {document.language}\n")
                f.write(f"File: {document.file_path}\n")
                f.write(f"Extracted on: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                f.write(text_content)
            
            logger.info(f"💾 Saved raw extracted text to: {raw_text_file}")
            
            # ========== PHASE 3: TEXT CLEANING ==========
            
            logger.info("Step 2/5: Cleaning text...")
            cleaned_text = await self.doc_processor.clean_text(text_content, document.language)
            logger.info(f"✅ Cleaned text: {len(cleaned_text)} characters")
            
            # Save cleaned text
            cleaned_text_file = extracted_text_dir / f"document_{document_id}_cleaned.txt"
            with open(cleaned_text_file, 'w', encoding='utf-8') as f:
                f.write(f"=== CLEANED TEXT FOR DOCUMENT {document_id} ===\n")
                f.write(f"Title: {document.title}\n")
                f.write(f"Language: {document.language}\n")
                f.write(f"File: {document.file_path}\n")
                f.write(f"Cleaned on: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                f.write(cleaned_text)
            
            logger.info(f"💾 Saved cleaned text to: {cleaned_text_file}")
            
            # ========== PHASE 3: TEXT CHUNKING ==========
            
            logger.info("Step 3/5: Chunking text (300-500 words)...")
            chunks_data = await self.doc_processor.chunk_text(
                cleaned_text,
                document.language,
                min_chunk_size=300,
                max_chunk_size=500,
                overlap=50
            )
            
            logger.info(f"✅ Created {len(chunks_data)} chunks")
            
            # Save chunked text to file
            chunks_text_file = extracted_text_dir / f"document_{document_id}_chunks.txt"
            with open(chunks_text_file, 'w', encoding='utf-8') as f:
                f.write(f"=== CHUNKED TEXT FOR DOCUMENT {document_id} ===\n")
                f.write(f"Title: {document.title}\n")
                f.write(f"Language: {document.language}\n")
                f.write(f"Total Chunks: {len(chunks_data)}\n")
                f.write(f"Chunked on: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, chunk_data in enumerate(chunks_data):
                    f.write(f"--- CHUNK {i+1} ---\n")
                    f.write(f"Chunk Index: {chunk_data['chunk_index']}\n")
                    f.write(f"Article Number: {chunk_data.get('article_number', 'N/A')}\n")
                    f.write(f"Section Title: {chunk_data.get('section_title', 'N/A')}\n")
                    f.write(f"Keywords: {', '.join(chunk_data.get('keywords', []))}\n")
                    f.write(f"Word Count: {len(chunk_data['content'].split())}\n")
                    f.write("-" * 40 + "\n")
                    f.write(chunk_data['content'])
                    f.write("\n\n" + "=" * 80 + "\n\n")
            
            logger.info(f"💾 Saved chunked text to: {chunks_text_file}")
            
            # Create chunk records
            created_chunks = []
            for chunk_data in chunks_data:
                chunk = await self.repository.create_chunk(
                    document_id=document_id,
                    chunk_index=chunk_data['chunk_index'],
                    content=chunk_data['content'],
                    article_number=chunk_data.get('article_number'),
                    section_title=chunk_data.get('section_title'),
                    keywords=chunk_data.get('keywords', [])
                )
                created_chunks.append(chunk)
            
            # ========== PHASE 4: GENERATE EMBEDDINGS ==========
            
            logger.info("Step 4/5: Generating embeddings...")
            chunk_texts = [chunk.content for chunk in created_chunks]
            embeddings = await self.embedding_service.generate_embeddings_batch(
                chunk_texts,
                batch_size=50
            )
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings")
            
            # Update chunks with embeddings
            for chunk, embedding in zip(created_chunks, embeddings):
                await self.repository.update_chunk_embedding(chunk.id, embedding)
            
            # ========== PHASE 4: ADD TO FAISS INDEX ==========
            
            logger.info("Step 5/5: Adding to FAISS index...")
            
            # Prepare batch data for FAISS
            chunk_embeddings = [
                (chunk.id, embedding)
                for chunk, embedding in zip(created_chunks, embeddings)
                if embedding and len(embedding) > 0
            ]
            
            # Add to FAISS index
            await self.faiss_service.add_batch_embeddings(chunk_embeddings)
            
            # Save FAISS index
            self.faiss_service.save_index()
            
            logger.info(f"✅ Added {len(chunk_embeddings)} vectors to FAISS index")
            
            # ========== MARK AS COMPLETE ==========
            
            await self.repository.update_document(
                document_id,
                is_processed=True,
                processing_status=ProcessingStatusEnum.DONE
            )
            
            logger.info(f"🎉 Document {document_id} processed successfully!")
            logger.info(f"   - {len(chunks_data)} chunks created")
            logger.info(f"   - {len(embeddings)} embeddings generated")
            logger.info(f"   - Indexed in FAISS")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing document {document_id}: {str(e)}")
            
            # Mark as error
            await self.repository.update_document(
                document_id,
                processing_status=ProcessingStatusEnum.ERROR
            )
            
            return False

    # ==================== PHASE 4: SEMANTIC SEARCH ====================

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        similarity_threshold: float = 0.5
    ) -> Tuple[List[Dict], float]:
        """
        Semantic search using FAISS vector similarity.
        
        Phase 4 Implementation:
        1. Generate query embedding
        2. Search in FAISS for Top-N similar vectors
        3. Fetch chunk and document metadata
        4. Return ranked results
        
        Args:
            query: Search query text
            top_k: Number of results to return
            document_type: Filter by document type
            language: Filter by language
            similarity_threshold: Minimum similarity score
            
        Returns:
            Tuple of (search results, query time in ms)
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Searching for: '{query[:50]}...'")
            
            # Generate query embedding
            logger.info("Generating query embedding...")
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            if not query_embedding or len(query_embedding) == 0:
                logger.error("Failed to generate query embedding")
                return [], 0.0
            
            # Search in FAISS
            logger.info(f"Searching FAISS index (top {top_k})...")
            results = await self.faiss_service.search(
                query_embedding=query_embedding,
                top_k=top_k,
                db=self.db,
                document_type=document_type,
                language=language,
                similarity_threshold=similarity_threshold
            )
            
            query_time = (time.time() - start_time) * 1000  # ms
            
            logger.info(f"✅ Found {len(results)} results in {query_time:.2f}ms")
            
            return results, query_time
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            query_time = (time.time() - start_time) * 1000
            return [], query_time

    async def search_for_case_analysis(
        self,
        case_text: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for similar legal cases/chunks for AI analysis.
        
        Phase 4: Ready for AI integration
        
        This method is specifically designed for AI case analysis:
        1. Input: New case text
        2. Generate embedding
        3. Find Top-N similar legal chunks
        4. Return results for AI to analyze
        
        Args:
            case_text: The case text to analyze
            top_k: Number of similar cases to return
            
        Returns:
            List of most relevant legal chunks for analysis
        """
        logger.info(f"🤖 AI Case Analysis: Searching for similar cases (top {top_k})")
        
        results, query_time = await self.semantic_search(
            query=case_text,
            top_k=top_k,
            similarity_threshold=0.6  # Higher threshold for case analysis
        )
        
        # Format results for AI analysis
        analysis_results = []
        for result in results:
            chunk = result['chunk']
            document = result['document']
            
            analysis_results.append({
                'relevance_score': result['similarity_score'],
                'legal_text': chunk.content,
                'article_number': chunk.article_number,
                'section_title': chunk.section_title,
                'source_document': document.title,
                'document_type': document.document_type,
                'language': document.language,
                'page_number': chunk.page_number,
                'reference': chunk.source_reference
            })
        
        logger.info(f"✅ Prepared {len(analysis_results)} legal references for AI analysis")
        
        return analysis_results

    # ==================== INDEX MANAGEMENT ====================

    async def rebuild_faiss_index(self):
        """
        Rebuild FAISS index from all chunks in database.
        
        Use this when:
        - Starting fresh
        - After many deletions
        - Index corrupted
        """
        logger.info("🔄 Rebuilding FAISS index from database...")
        
        await self.faiss_service.rebuild_index(self.db)
        
        logger.info("✅ FAISS index rebuilt successfully")

    async def initialize_faiss_index(self):
        """
        Initialize FAISS index at startup.
        
        Tries to load existing index, or builds from database if not found.
        """
        logger.info("Initializing FAISS index...")
        
        # Try to load existing index
        loaded = self.faiss_service.load_index()
        
        if loaded:
            logger.info("✅ Loaded existing FAISS index")
        else:
            logger.info("No existing index found. Building from database...")
            await self.faiss_service.build_index_from_database(self.db)
            self.faiss_service.save_index()
            logger.info("✅ Built and saved new FAISS index")

    def get_faiss_stats(self) -> Dict:
        """
        Get FAISS index statistics.
        
        Returns:
            Dictionary with index stats
        """
        return self.faiss_service.get_index_stats()

    # ==================== UTILITY METHODS ====================

    async def get_document(self, document_id: int) -> Optional[LegalDocument]:
        """Get document by ID."""
        return await self.repository.get_document_by_id(document_id)

    async def get_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        processing_status: Optional[str] = None
    ) -> Tuple[List[LegalDocument], int]:
        """Get documents with pagination and filtering."""
        skip = (page - 1) * page_size
        
        return await self.repository.get_documents(
            skip=skip,
            limit=page_size,
            document_type=document_type,
            language=language,
            processing_status=processing_status
        )

    async def delete_document(self, document_id: int) -> bool:
        """
        Delete document and remove from FAISS index.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        # Get document to delete file
        document = await self.repository.get_document_by_id(document_id)
        if not document:
            return False
        
        # Get chunk IDs for FAISS removal
        chunks = await self.repository.get_chunks_by_document(document_id, limit=10000)
        
        # Remove from FAISS index
        for chunk in chunks:
            await self.faiss_service.remove_chunk_embedding(chunk.id)
        
        # Delete from database (cascades to chunks)
        success = await self.repository.delete_document(document_id)
        
        if success:
            # Delete file from disk
            try:
                file_path = Path(document.file_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted file: {document.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {document.file_path}: {str(e)}")
            
            # Save updated FAISS index
            self.faiss_service.save_index()
        
        return success

    async def get_processing_progress(self, document_id: int) -> Dict:
        """
        Get processing progress for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            Progress information
        """
        document = await self.repository.get_document_by_id(document_id)
        if not document:
            return {
                'document_id': document_id,
                'status': 'not_found',
                'progress_percentage': 0.0,
                'message': 'Document not found'
            }
        
        # Count chunks
        chunks = await self.repository.get_chunks_by_document(document_id, limit=10000)
        chunks_with_embeddings = sum(1 for chunk in chunks if chunk.embedding and len(chunk.embedding) > 0)
        
        # Calculate progress
        if document.processing_status == ProcessingStatusEnum.DONE:
            progress = 100.0
            message = "Processing complete"
        elif document.processing_status == ProcessingStatusEnum.ERROR:
            progress = 0.0
            message = "Processing failed"
        elif document.processing_status == ProcessingStatusEnum.PROCESSING:
            if len(chunks) > 0:
                progress = (chunks_with_embeddings / len(chunks)) * 100
                message = f"Processing chunks: {chunks_with_embeddings}/{len(chunks)}"
            else:
                progress = 50.0
                message = "Extracting and chunking text..."
        else:  # pending
            progress = 0.0
            message = "Waiting to process"
        
        return {
            'document_id': document_id,
            'status': document.processing_status.value if hasattr(document.processing_status, 'value') else str(document.processing_status),
            'progress_percentage': progress,
            'chunks_processed': chunks_with_embeddings,
            'total_chunks': len(chunks),
            'message': message
        }

    async def get_statistics(self) -> Dict:
        """
        Get statistics about the legal document system.
        
        Returns:
            Dictionary with statistics
        """
        db_stats = await self.repository.get_document_stats()
        faiss_stats = self.get_faiss_stats()
        
        return {
            **db_stats,
            'faiss_index': faiss_stats,
            'embedding_provider': self.embedding_service.provider,
            'embedding_dimension': self.embedding_service.embedding_dimension
        }

