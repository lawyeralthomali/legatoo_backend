"""
Legal Document Repository for data access layer.

This module implements the Repository pattern for legal documents and chunks,
providing clean separation of data access logic from business logic.
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
import logging

from ..models.legal_document2 import LegalDocument, LegalDocumentChunk
from .base import BaseRepository

logger = logging.getLogger(__name__)


class LegalDocumentRepository:
    """Repository for legal document operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize legal document repository.
        
        Args:
            db: Database session
        """
        self.db = db

    async def create_document(
        self, 
        title: str,
        file_path: str,
        document_type: str,
        language: str,
        uploaded_by_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> LegalDocument:
        """
        Create a new legal document.
        
        Args:
            title: Document title
            file_path: Path to the uploaded file
            document_type: Type of document
            language: Document language
            uploaded_by_id: ID of the user who uploaded
            notes: Additional notes
            
        Returns:
            Created LegalDocument instance
        """
        from ..models.legal_document2 import ProcessingStatusEnum, DocumentTypeEnum, LanguageEnum
        
        # Convert string values to enum values
        doc_type_enum = DocumentTypeEnum(document_type) if document_type else DocumentTypeEnum.OTHER
        lang_enum = LanguageEnum(language) if language else LanguageEnum.ARABIC
        
        document = LegalDocument(
            title=title,
            file_path=file_path,
            document_type=doc_type_enum,
            language=lang_enum,
            uploaded_by_id=uploaded_by_id,
            notes=notes,
            is_processed=False,
            processing_status=ProcessingStatusEnum.PENDING
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        logger.info(f"Created document {document.id}: {title}")
        return document

    async def get_document_by_id(self, document_id: int) -> Optional[LegalDocument]:
        """
        Get document by ID with chunks preloaded.
        
        Args:
            document_id: Document ID
            
        Returns:
            LegalDocument instance or None
        """
        result = await self.db.execute(
            select(LegalDocument)
            .options(selectinload(LegalDocument.chunks))
            .where(LegalDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        processing_status: Optional[str] = None,
        uploaded_by_id: Optional[int] = None
    ) -> Tuple[List[LegalDocument], int]:
        """
        Get documents with filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            document_type: Filter by document type
            language: Filter by language
            processing_status: Filter by processing status
            uploaded_by_id: Filter by uploader
            
        Returns:
            Tuple of (documents list, total count)
        """
        # Build query with filters
        query = select(LegalDocument)
        count_query = select(func.count()).select_from(LegalDocument)
        
        filters = []
        if document_type:
            from ..models.legal_document2 import DocumentTypeEnum
            try:
                doc_type_enum = DocumentTypeEnum(document_type)
                filters.append(LegalDocument.document_type == doc_type_enum)
            except ValueError:
                pass
        if language:
            from ..models.legal_document2 import LanguageEnum
            try:
                lang_enum = LanguageEnum(language)
                filters.append(LegalDocument.language == lang_enum)
            except ValueError:
                pass
        if processing_status:
            from ..models.legal_document2 import ProcessingStatusEnum
            try:
                status_enum = ProcessingStatusEnum(processing_status)
                filters.append(LegalDocument.processing_status == status_enum)
            except ValueError:
                pass
        if uploaded_by_id:
            filters.append(LegalDocument.uploaded_by_id == uploaded_by_id)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Get documents with pagination and chunks
        query = query.options(selectinload(LegalDocument.chunks)).order_by(desc(LegalDocument.created_at)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        documents = result.scalars().all()
        
        return documents, total

    async def update_document(
        self,
        document_id: int,
        **kwargs
    ) -> Optional[LegalDocument]:
        """
        Update document fields.
        
        Args:
            document_id: Document ID
            **kwargs: Fields to update
            
        Returns:
            Updated LegalDocument or None
        """
        document = await self.get_document_by_id(document_id)
        if not document:
            return None
        
        for key, value in kwargs.items():
            if hasattr(document, key) and value is not None:
                setattr(document, key, value)
        
        await self.db.commit()
        await self.db.refresh(document)
        logger.info(f"Updated document {document_id}")
        return document

    async def delete_document(self, document_id: int) -> bool:
        """
        Delete document and all its chunks.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        document = await self.get_document_by_id(document_id)
        if not document:
            return False
        
        await self.db.delete(document)
        await self.db.commit()
        logger.info(f"Deleted document {document_id}")
        return True

    async def create_chunk(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        article_number: Optional[str] = None,
        section_title: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None
    ) -> LegalDocumentChunk:
        """
        Create a document chunk.
        
        Args:
            document_id: Parent document ID
            chunk_index: Index of the chunk
            content: Chunk text content
            article_number: Detected article number
            section_title: Detected section title
            keywords: Extracted keywords
            embedding: Vector embedding
            
        Returns:
            Created LegalDocumentChunk instance
        """
        chunk = LegalDocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            article_number=article_number,
            section_title=section_title,
            keywords=keywords or [],
            embedding=embedding or []
        )
        self.db.add(chunk)
        await self.db.commit()
        await self.db.refresh(chunk)
        return chunk

    async def get_chunk_by_id(self, chunk_id: int) -> Optional[LegalDocumentChunk]:
        """
        Get chunk by ID with document preloaded.
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            LegalDocumentChunk instance or None
        """
        result = await self.db.execute(
            select(LegalDocumentChunk)
            .options(selectinload(LegalDocumentChunk.document))
            .where(LegalDocumentChunk.id == chunk_id)
        )
        return result.scalar_one_or_none()

    async def get_chunks_by_document(
        self,
        document_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[LegalDocumentChunk]:
        """
        Get chunks for a specific document.
        
        Args:
            document_id: Document ID
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            List of LegalDocumentChunk instances
        """
        result = await self.db.execute(
            select(LegalDocumentChunk)
            .where(LegalDocumentChunk.document_id == document_id)
            .order_by(LegalDocumentChunk.chunk_index)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_chunk_embedding(
        self,
        chunk_id: int,
        embedding: List[float]
    ) -> Optional[LegalDocumentChunk]:
        """
        Update chunk embedding vector.
        
        Args:
            chunk_id: Chunk ID
            embedding: Vector embedding
            
        Returns:
            Updated chunk or None
        """
        chunk = await self.get_chunk_by_id(chunk_id)
        if not chunk:
            return None
        
        chunk.embedding = embedding
        await self.db.commit()
        await self.db.refresh(chunk)
        return chunk

    async def search_chunks_by_filters(
        self,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        article_number: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[LegalDocumentChunk]:
        """
        Search chunks with keyword-based filtering.
        
        Args:
            document_type: Filter by document type
            language: Filter by language
            article_number: Filter by article number
            keywords: Filter by keywords
            limit: Maximum number of results
            
        Returns:
            List of matching chunks
        """
        query = (
            select(LegalDocumentChunk)
            .join(LegalDocument)
            .options(selectinload(LegalDocumentChunk.document))
        )
        
        filters = []
        if document_type:
            filters.append(LegalDocument.document_type == document_type)
        if language:
            filters.append(LegalDocument.language == language)
        if article_number:
            filters.append(LegalDocumentChunk.article_number == article_number)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_document_stats(self) -> Dict[str, Any]:
        """
        Get statistics about documents and chunks.
        
        Returns:
            Dictionary containing statistics
        """
        # Total documents
        total_docs_result = await self.db.execute(
            select(func.count()).select_from(LegalDocument)
        )
        total_documents = total_docs_result.scalar_one()
        
        # Total chunks
        total_chunks_result = await self.db.execute(
            select(func.count()).select_from(LegalDocumentChunk)
        )
        total_chunks = total_chunks_result.scalar_one()
        
        # Documents by type
        docs_by_type_result = await self.db.execute(
            select(LegalDocument.document_type, func.count())
            .group_by(LegalDocument.document_type)
        )
        documents_by_type = {row[0]: row[1] for row in docs_by_type_result}
        
        # Documents by language
        docs_by_lang_result = await self.db.execute(
            select(LegalDocument.language, func.count())
            .group_by(LegalDocument.language)
        )
        documents_by_language = {row[0]: row[1] for row in docs_by_lang_result}
        
        # Documents by processing status
        docs_by_status_result = await self.db.execute(
            select(LegalDocument.processing_status, func.count())
            .group_by(LegalDocument.processing_status)
        )
        status_counts = {row[0]: row[1] for row in docs_by_status_result}
        
        return {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "documents_by_type": documents_by_type,
            "documents_by_language": documents_by_language,
            "processing_pending": status_counts.get("pending", 0),
            "processing_done": status_counts.get("done", 0),
            "processing_error": status_counts.get("error", 0)
        }

    async def get_adjacent_chunks(
        self,
        chunk_id: int
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Get previous and next chunk IDs for navigation.
        
        Args:
            chunk_id: Current chunk ID
            
        Returns:
            Tuple of (previous_chunk_id, next_chunk_id)
        """
        chunk = await self.get_chunk_by_id(chunk_id)
        if not chunk:
            return None, None
        
        # Get previous chunk
        prev_result = await self.db.execute(
            select(LegalDocumentChunk.id)
            .where(
                and_(
                    LegalDocumentChunk.document_id == chunk.document_id,
                    LegalDocumentChunk.chunk_index < chunk.chunk_index
                )
            )
            .order_by(desc(LegalDocumentChunk.chunk_index))
            .limit(1)
        )
        prev_id = prev_result.scalar_one_or_none()
        
        # Get next chunk
        next_result = await self.db.execute(
            select(LegalDocumentChunk.id)
            .where(
                and_(
                    LegalDocumentChunk.document_id == chunk.document_id,
                    LegalDocumentChunk.chunk_index > chunk.chunk_index
                )
            )
            .order_by(LegalDocumentChunk.chunk_index)
            .limit(1)
        )
        next_id = next_result.scalar_one_or_none()
        
        return prev_id, next_id

