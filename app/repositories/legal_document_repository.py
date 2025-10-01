"""
Legal Document Repository for data access operations.

This module handles all database operations related to legal documents
and document chunks, following the Repository pattern.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID

from ..models.legal_document import LegalDocument, LegalDocumentChunk
from .base import BaseRepository


class LegalDocumentRepository(BaseRepository):
    """Repository for legal document data access operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize legal document repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, LegalDocument)
    
    async def get_chunks_with_embeddings(self) -> List[LegalDocumentChunk]:
        """
        Get all document chunks that have embeddings.
        
        Returns:
            List of LegalDocumentChunk objects with embeddings
        """
        result = await self.db.execute(
            select(LegalDocumentChunk)
            .join(LegalDocument)
            .where(
                and_(
                    LegalDocumentChunk.embedding.isnot(None),
                    LegalDocumentChunk.embedding != []
                )
            )
        )
        return result.scalars().all()
    
    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[LegalDocumentChunk]:
        """
        Get a specific document chunk by ID.
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            LegalDocumentChunk if found, None otherwise
        """
        result = await self.db.execute(
            select(LegalDocumentChunk)
            .where(LegalDocumentChunk.id == chunk_id)
        )
        return result.scalar_one_or_none()
    
    async def get_document_by_id(self, document_id: UUID) -> Optional[LegalDocument]:
        """
        Get a legal document by ID with its chunks.
        
        Args:
            document_id: Document ID
            
        Returns:
            LegalDocument if found, None otherwise
        """
        result = await self.db.execute(
            select(LegalDocument)
            .where(LegalDocument.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def get_documents_by_type(
        self, 
        document_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[LegalDocument]:
        """
        Get documents filtered by type.
        
        Args:
            document_type: Type of document to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of LegalDocument objects
        """
        result = await self.db.execute(
            select(LegalDocument)
            .where(LegalDocument.document_type == document_type)
            .offset(skip)
            .limit(limit)
            .order_by(LegalDocument.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_documents_by_language(
        self, 
        language: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[LegalDocument]:
        """
        Get documents filtered by language.
        
        Args:
            language: Language to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of LegalDocument objects
        """
        result = await self.db.execute(
            select(LegalDocument)
            .where(LegalDocument.language == language)
            .offset(skip)
            .limit(limit)
            .order_by(LegalDocument.created_at.desc())
        )
        return result.scalars().all()
    
    async def search_documents_by_title(
        self, 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[LegalDocument]:
        """
        Search documents by title.
        
        Args:
            search_term: Term to search for in document titles
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of LegalDocument objects matching the search term
        """
        result = await self.db.execute(
            select(LegalDocument)
            .where(LegalDocument.title.ilike(f"%{search_term}%"))
            .offset(skip)
            .limit(limit)
            .order_by(LegalDocument.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_recent_documents(
        self, 
        days: int = 30, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[LegalDocument]:
        """
        Get documents created within the last N days.
        
        Args:
            days: Number of days to look back
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recent LegalDocument objects
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = await self.db.execute(
            select(LegalDocument)
            .where(LegalDocument.created_at >= cutoff_date)
            .offset(skip)
            .limit(limit)
            .order_by(LegalDocument.created_at.desc())
        )
        return result.scalars().all()
    
    async def count_documents(self) -> int:
        """
        Count total number of documents.
        
        Returns:
            Total count of documents
        """
        result = await self.db.execute(select(LegalDocument))
        return len(result.scalars().all())
    
    async def count_chunks_with_embeddings(self) -> int:
        """
        Count number of chunks that have embeddings.
        
        Returns:
            Count of chunks with embeddings
        """
        result = await self.db.execute(
            select(LegalDocumentChunk)
            .where(
                and_(
                    LegalDocumentChunk.embedding.isnot(None),
                    LegalDocumentChunk.embedding != []
                )
            )
        )
        return len(result.scalars().all())
