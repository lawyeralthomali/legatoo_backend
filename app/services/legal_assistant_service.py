"""
Legal Assistant Service - Main orchestration layer.

This service coordinates document processing, embedding generation,
and search operations for the Legal AI Assistant.
"""

import logging
import os
import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.legal_document_repository import LegalDocumentRepository
from .document_processing_service import DocumentProcessingService
from .embedding_service import EmbeddingService
from .semantic_search_service import SemanticSearchService
from ..models.legal_document2 import LegalDocument, LegalDocumentChunk

logger = logging.getLogger(__name__)


class LegalAssistantService:
    """Main service for legal assistant operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize legal assistant service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = LegalDocumentRepository(db)
        self.doc_processor = DocumentProcessingService()
        self.embedding_service = EmbeddingService()
        self.search_service = SemanticSearchService(
            self.repository,
            self.embedding_service
        )
        
        # Configuration
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads/legal_documents"))
        self.allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_document(
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
        Upload and optionally process a legal document.
        
        Args:
            file_path: Path to the uploaded file
            original_filename: Original name of the file
            title: Document title
            document_type: Type of document
            language: Document language
            uploaded_by_id: ID of the user who uploaded
            notes: Additional notes
            process_immediately: Whether to process immediately or queue
            
        Returns:
            Created LegalDocument instance
            
        Raises:
            ValueError: If file format is invalid
        """
        # Validate file format
        file_extension = Path(original_filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
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
        
        logger.info(f"Document {document.id} uploaded: {title}")
        
        # Process document if requested
        if process_immediately:
            # Process asynchronously in background
            asyncio.create_task(self.process_document(document.id))
        
        return document

    async def process_document(self, document_id: int) -> bool:
        """
        Process a document: extract text, chunk, generate embeddings.
        
        This is the main processing pipeline for legal documents.
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update status to processing
            await self.repository.update_document(
                document_id,
                processing_status="processing"
            )
            
            # Get document
            document = await self.repository.get_document_by_id(document_id)
            if not document:
                logger.error(f"Document {document_id} not found")
                return False
            
            logger.info(f"Starting processing for document {document_id}")
            
            # Step 1: Extract text
            file_extension = Path(document.file_path).suffix
            text_content = await self.doc_processor.extract_text_from_file(
                document.file_path,
                file_extension
            )
            
            if not text_content or len(text_content.strip()) < 100:
                raise ValueError("Extracted text is too short or empty")
            
            logger.info(f"Extracted {len(text_content)} characters from document {document_id}")
            
            # Step 2: Detect language if not specified or verify
            detected_language = await self.doc_processor.detect_document_language(text_content[:1000])
            if document.language == 'ar' and detected_language != 'ar':
                logger.warning(f"Language mismatch for document {document_id}")
            
            # Step 3: Chunk the text
            chunks_data = await self.doc_processor.chunk_text(
                text_content,
                document.language,
                min_chunk_size=200,
                max_chunk_size=500,
                overlap=50
            )
            
            logger.info(f"Created {len(chunks_data)} chunks for document {document_id}")
            
            # Step 4: Create chunk records
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
            
            # Step 5: Generate embeddings for all chunks
            chunk_texts = [chunk.content for chunk in created_chunks]
            embeddings = await self.embedding_service.generate_embeddings_batch(
                chunk_texts,
                batch_size=50
            )
            
            logger.info(f"Generated {len(embeddings)} embeddings for document {document_id}")
            
            # Step 6: Update chunks with embeddings
            for chunk, embedding in zip(created_chunks, embeddings):
                await self.repository.update_chunk_embedding(chunk.id, embedding)
            
            # Step 7: Mark document as processed
            await self.repository.update_document(
                document_id,
                is_processed=True,
                processing_status="done"
            )
            
            logger.info(f"Successfully processed document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            
            # Mark as error
            await self.repository.update_document(
                document_id,
                processing_status="error"
            )
            
            return False

    async def search_documents(
        self,
        query: str,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        article_number: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.5
    ) -> Tuple[List[Dict], float]:
        """
        Search legal documents using semantic search.
        
        Args:
            query: Search query
            document_type: Filter by document type
            language: Filter by language
            article_number: Filter by article number
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            Tuple of (search results with metadata, query time in ms)
        """
        results, query_time = await self.search_service.search(
            query=query,
            document_type=document_type,
            language=language,
            article_number=article_number,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        # Enhance results with document metadata
        enhanced_results = []
        for result in results:
            chunk = result['chunk']
            
            # Get document (should be preloaded)
            document = await self.repository.get_document_by_id(chunk.document_id)
            
            enhanced_results.append({
                'chunk': chunk,
                'document': document,
                'similarity_score': result['similarity_score'],
                'highlights': result['highlights']
            })
        
        return enhanced_results, query_time

    async def get_document(self, document_id: int) -> Optional[LegalDocument]:
        """
        Get document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            LegalDocument instance or None
        """
        return await self.repository.get_document_by_id(document_id)

    async def get_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        processing_status: Optional[str] = None,
        uploaded_by_id: Optional[int] = None
    ) -> Tuple[List[LegalDocument], int]:
        """
        Get documents with pagination and filtering.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            document_type: Filter by document type
            language: Filter by language
            processing_status: Filter by processing status
            uploaded_by_id: Filter by uploader
            
        Returns:
            Tuple of (documents list, total count)
        """
        skip = (page - 1) * page_size
        
        return await self.repository.get_documents(
            skip=skip,
            limit=page_size,
            document_type=document_type,
            language=language,
            processing_status=processing_status,
            uploaded_by_id=uploaded_by_id
        )

    async def update_document(
        self,
        document_id: int,
        title: Optional[str] = None,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        notes: Optional[str] = None,
        reprocess: bool = False
    ) -> Optional[LegalDocument]:
        """
        Update document metadata.
        
        Args:
            document_id: Document ID
            title: Updated title
            document_type: Updated document type
            language: Updated language
            notes: Updated notes
            reprocess: Whether to reprocess the document
            
        Returns:
            Updated LegalDocument or None
        """
        update_data = {}
        
        if title is not None:
            update_data['title'] = title
        if document_type is not None:
            update_data['document_type'] = document_type
        if language is not None:
            update_data['language'] = language
        if notes is not None:
            update_data['notes'] = notes
        
        document = await self.repository.update_document(document_id, **update_data)
        
        # Reprocess if language changed or requested
        if document and reprocess:
            asyncio.create_task(self.process_document(document_id))
        
        return document

    async def delete_document(self, document_id: int) -> bool:
        """
        Delete document and all its chunks.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        # Get document to delete file
        document = await self.repository.get_document_by_id(document_id)
        if not document:
            return False
        
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
        
        return success

    async def get_chunk(self, chunk_id: int) -> Optional[Dict]:
        """
        Get chunk by ID with navigation information.
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            Dictionary with chunk, document, and adjacent chunk IDs
        """
        chunk = await self.repository.get_chunk_by_id(chunk_id)
        if not chunk:
            return None
        
        # Get adjacent chunks
        prev_id, next_id = await self.repository.get_adjacent_chunks(chunk_id)
        
        # Get document
        document = await self.repository.get_document_by_id(chunk.document_id)
        
        return {
            'chunk': chunk,
            'document': document,
            'previous_chunk_id': prev_id,
            'next_chunk_id': next_id
        }

    async def get_document_chunks(
        self,
        document_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> List[LegalDocumentChunk]:
        """
        Get chunks for a specific document.
        
        Args:
            document_id: Document ID
            page: Page number
            page_size: Items per page
            
        Returns:
            List of chunks
        """
        skip = (page - 1) * page_size
        
        return await self.repository.get_chunks_by_document(
            document_id,
            skip=skip,
            limit=page_size
        )

    async def get_statistics(self) -> Dict:
        """
        Get statistics about the legal document system.
        
        Returns:
            Dictionary with statistics
        """
        return await self.repository.get_document_stats()

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
        if document.processing_status == 'done':
            progress = 100.0
            message = "Processing complete"
        elif document.processing_status == 'error':
            progress = 0.0
            message = "Processing failed"
        elif document.processing_status == 'processing':
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
            'status': document.processing_status,
            'progress_percentage': progress,
            'chunks_processed': chunks_with_embeddings,
            'total_chunks': len(chunks),
            'message': message
        }

