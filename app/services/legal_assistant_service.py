"""
Legal Assistant Service - Main orchestration layer (Updated for Phase 3 & 4).

This service coordinates document processing, embedding generation,
and search operations for the Legal AI Assistant.

✅ Phase 3 & 4 Integration:
- Uses CompleteLegalAIService for enhanced document processing
- Supports multi-format files (PDF, DOCX, Images with OCR)
- FAISS vector search for fast semantic search
- Real-time processing with progress tracking
"""

import logging
import os
import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.legal_document_repository import LegalDocumentRepository
from .complete_legal_ai_service import CompleteLegalAIService
from ..models.legal_document2 import LegalDocument, LegalDocumentChunk

logger = logging.getLogger(__name__)


class LegalAssistantService:
    """
    Main service for legal assistant operations.
    
    ✅ Updated to use Phase 3 & 4 implementation (CompleteLegalAIService)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize legal assistant service.
        
        Args:
            db: Database session
        """
        self.db = db
        
        # ✅ NEW: Use CompleteLegalAIService (Phase 3 & 4)
        self.ai_service = CompleteLegalAIService(db)
        
        # Keep repository for direct access if needed
        self.repository = self.ai_service.repository
        
        # Configuration
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "uploads/legal_documents"))
        
        # ✅ UPDATED: Support more formats (including images for OCR)
        self.allowed_extensions = ['.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png']
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("LegalAssistantService initialized with Phase 3 & 4 support")

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
        
        ✅ Phase 3 & 4: Now supports PDF, DOCX, Images (OCR), TXT
        
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
        
        # ✅ Use CompleteLegalAIService (Phase 3 & 4)
        document = await self.ai_service.upload_and_process_document(
            file_path=file_path,
            original_filename=original_filename,
            title=title,
            document_type=document_type,
            language=language,
            uploaded_by_id=uploaded_by_id,
            notes=notes,
            process_immediately=process_immediately
        )
        
        logger.info(f"✅ Document {document.id} uploaded with Phase 3 & 4: {title}")
        
        return document

    async def process_document(self, document_id: int) -> bool:
        """
        Process a document: extract text, chunk, generate embeddings.
        
        ✅ Phase 3 & 4: Enhanced processing with OCR, FAISS indexing
        
        This is the main processing pipeline for legal documents:
        1. Extract text (PDF/DOCX/Images with OCR)
        2. Clean and normalize text
        3. Intelligent chunking (300-500 words)
        4. Generate embeddings
        5. Add to FAISS index
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            True if successful, False otherwise
        """
        # ✅ Use CompleteLegalAIService (Phase 3 & 4)
        return await self.ai_service.process_document(document_id)

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
        
        ✅ Phase 4: Now uses FAISS vector search for faster results
        
        Args:
            query: Search query
            document_type: Filter by document type
            language: Filter by language
            article_number: Filter by article number (optional, for post-filtering)
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            Tuple of (search results with metadata, query time in ms)
        """
        # ✅ Use CompleteLegalAIService with FAISS search (Phase 4)
        results, query_time = await self.ai_service.semantic_search(
            query=query,
            top_k=limit,
            document_type=document_type,
            language=language,
            similarity_threshold=similarity_threshold
        )
        
        # Post-filter by article number if specified
        if article_number and results:
            results = [
                r for r in results 
                if r.get('chunk') and r['chunk'].article_number == article_number
            ]
        
        # Add highlights (empty for now, can be enhanced later)
        for result in results:
            if 'highlights' not in result:
                result['highlights'] = []
        
        return results, query_time

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
        uploaded_by_id: Optional[int] = None,
        search: Optional[str] = None
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
            search: Search term for document titles
            
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
            uploaded_by_id=uploaded_by_id,
            search=search
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
        
        ✅ Phase 4: Also removes vectors from FAISS index
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        # ✅ Use CompleteLegalAIService (removes from FAISS too)
        return await self.ai_service.delete_document(document_id)

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
        
        ✅ Phase 4: Now includes FAISS index statistics
        
        Returns:
            Dictionary with statistics including:
            - Total documents/chunks
            - Processing status counts
            - FAISS index info (vectors, dimension, etc.)
            - Embedding provider info
        """
        # ✅ Use CompleteLegalAIService (includes FAISS stats)
        return await self.ai_service.get_statistics()

    async def get_processing_progress(self, document_id: int) -> Dict:
        """
        Get processing progress for a document.
        
        ✅ Phase 3 & 4: Enhanced progress tracking
        
        Args:
            document_id: Document ID
            
        Returns:
            Progress information with detailed status
        """
        # ✅ Use CompleteLegalAIService
        return await self.ai_service.get_processing_progress(document_id)

    async def get_document_statistics(self) -> Dict:
        """
        Get comprehensive document statistics.
        
        Returns:
            Dictionary with document statistics including counts by type, language, etc.
        """
        try:
            # Get basic statistics from repository
            stats = await self.repository.get_statistics()
            
            # Add additional statistics
            documents, _ = await self.repository.get_documents(skip=0, limit=1000)
            
            # Count by document type
            documents_by_type = {}
            documents_by_language = {}
            processing_counts = {"pending": 0, "processing": 0, "done": 0, "error": 0}
            
            for doc in documents:
                # Count by type
                doc_type = doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type)
                documents_by_type[doc_type] = documents_by_type.get(doc_type, 0) + 1
                
                # Count by language
                lang = doc.language.value if hasattr(doc.language, 'value') else str(doc.language)
                documents_by_language[lang] = documents_by_language.get(lang, 0) + 1
                
                # Count by processing status
                status = doc.processing_status.value if hasattr(doc.processing_status, 'value') else str(doc.processing_status)
                processing_counts[status] = processing_counts.get(status, 0) + 1
            
            # Get total chunks count
            total_chunks = sum(len(doc.chunks) if doc.chunks else 0 for doc in documents)
            
            return {
                "total_documents": len(documents),
                "total_chunks": total_chunks,
                "documents_by_type": documents_by_type,
                "documents_by_language": documents_by_language,
                "processing_pending": processing_counts["pending"],
                "processing_done": processing_counts["done"],
                "processing_error": processing_counts["error"],
                "processing_in_progress": processing_counts["processing"]
            }
            
        except Exception as e:
            logger.error(f"Error getting document statistics: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "documents_by_type": {},
                "documents_by_language": {},
                "processing_pending": 0,
                "processing_done": 0,
                "processing_error": 0,
                "processing_in_progress": 0
            }

