"""
Legal Document models for FastAPI - Enhanced version with Enum types and improved indexing.

This module defines the database models for legal document storage and processing:
- LegalDocument: Main document metadata with enum-based type safety
- LegalDocumentChunk: Document chunks with embeddings for semantic search

Updates:
- Converted String fields to Enum types for better type safety
- Added page tracking and source reference fields
- Optimized indexing for search performance
- Maintained compatibility with SQLite
"""
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, JSON, Enum, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base


class DocumentTypeEnum(enum.Enum):
    """
    Document type enumeration for legal documents.
    
    Provides type safety and ensures only valid document types are stored.
    """
    EMPLOYMENT_CONTRACT = "employment_contract"
    PARTNERSHIP_CONTRACT = "partnership_contract"
    SERVICE_CONTRACT = "service_contract"
    LEASE_CONTRACT = "lease_contract"
    SALES_CONTRACT = "sales_contract"
    LABOR_LAW = "labor_law"
    COMMERCIAL_LAW = "commercial_law"
    CIVIL_LAW = "civil_law"
    OTHER = "other"


class LanguageEnum(enum.Enum):
    """
    Language enumeration for multilingual support.
    
    Supports Arabic, English, and French legal documents.
    """
    ARABIC = "ar"
    ENGLISH = "en"
    FRENCH = "fr"


class ProcessingStatusEnum(enum.Enum):
    """
    Processing status enumeration for document processing pipeline.
    
    Tracks the current state of document processing:
    - PENDING: Awaiting processing
    - PROCESSING: Currently being processed
    - DONE: Successfully processed
    - ERROR: Processing failed
    """
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class LegalDocument(Base):
    """
    Model for storing legal documents with enhanced type safety.
    
    Stores metadata about uploaded legal documents and tracks their processing status.
    Uses Enum types for document_type, language, and processing_status to ensure
    data integrity and prevent invalid values.
    
    Relationships:
    - uploaded_by: Links to User who uploaded the document
    - chunks: One-to-many relationship with LegalDocumentChunk (cascade delete)
    """
    __tablename__ = "legal_documents"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Document metadata
    title = Column(String(255), nullable=False, comment="Document title")
    file_path = Column(String(500), nullable=False, comment="Path to stored file on disk")
    notes = Column(Text, nullable=True, comment="Optional notes about the document")
    
    # Foreign key to User (updated from Profile to User)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="User who uploaded the document")
    
    # Enum fields for type safety (converted from String to Enum)
    document_type = Column(
        Enum(DocumentTypeEnum),
        default=DocumentTypeEnum.OTHER,
        nullable=False,
        comment="Type of legal document (Enum for type safety)"
    )
    language = Column(
        Enum(LanguageEnum),
        default=LanguageEnum.ARABIC,
        nullable=False,
        comment="Document language (Enum for type safety)"
    )
    processing_status = Column(
        Enum(ProcessingStatusEnum),
        default=ProcessingStatusEnum.PENDING,
        nullable=False,
        comment="Current processing status (Enum for type safety)"
    )
    
    # Processing flags
    is_processed = Column(Boolean, default=False, nullable=False, comment="Whether document processing is complete")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="Creation timestamp")
    
    # Relationships
    uploaded_by = relationship(
        "User",
        back_populates="uploaded_documents",
        lazy="select",
        doc="User who uploaded this document"
    )
    chunks = relationship(
        "LegalDocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="select",
        doc="Text chunks extracted from this document"
    )
    
    @property
    def file_url(self) -> str:
        """
        Return the URL for accessing the file.
        
        Returns:
            str: URL path to the document file
        """
        return f"/media/{self.file_path}"
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<LegalDocument(id={self.id}, title='{self.title}', type={self.document_type.value}, status={self.processing_status.value})>"


class LegalDocumentChunk(Base):
    """
    Model for storing chunks of legal documents with embeddings.
    
    Stores intelligently chunked text segments from legal documents along with:
    - Embeddings for semantic search (3072-dim vectors stored as JSON)
    - Legal entity metadata (article numbers, sections)
    - Keywords for hybrid search
    - Page numbers and source references for traceability
    
    Enhanced with:
    - page_number: Optional page tracking for document navigation
    - source_reference: Optional citation/reference to original source
    - Composite index on (document_id, chunk_index) for optimized queries
    
    Relationships:
    - document: Links back to parent LegalDocument
    """
    __tablename__ = "legal_document_chunks"
    
    # Define composite index for optimized chunk retrieval
    __table_args__ = (
        Index('idx_document_chunk', 'document_id', 'chunk_index'),
        {'comment': 'Stores text chunks with embeddings for semantic search'}
    )
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Foreign key to parent document
    document_id = Column(
        Integer,
        ForeignKey("legal_documents.id"),
        nullable=False,
        comment="Reference to parent document"
    )
    
    # Chunk positioning and content
    chunk_index = Column(Integer, nullable=False, comment="Sequential index of chunk within document")
    content = Column(Text, nullable=False, comment="Text content of this chunk")
    
    # NEW: Page tracking for document navigation
    page_number = Column(
        Integer,
        nullable=True,
        comment="Optional page number where this chunk appears (for PDF navigation)"
    )
    
    # NEW: Source reference for citation
    source_reference = Column(
        String(255),
        nullable=True,
        comment="Optional reference to original source (e.g., 'Labor Law 2023, Article 109')"
    )
    
    # Legal entity metadata
    article_number = Column(String(50), nullable=True, comment="Extracted article number (e.g., '109')")
    section_title = Column(String(255), nullable=True, comment="Extracted section title (e.g., 'الباب السادس')")
    
    # Search optimization fields
    keywords = Column(
        JSON,
        default=list,
        nullable=True,
        comment="Extracted keywords as JSON array (for hybrid search)"
    )
    embedding = Column(
        JSON,
        default=list,
        nullable=True,
        comment="Embedding vector as JSON array [3072 floats] (for semantic search)"
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="Creation timestamp")
    
    # Relationships
    document = relationship(
        "LegalDocument",
        back_populates="chunks",
        lazy="select",
        doc="Parent document this chunk belongs to"
    )
    
    def add_keyword(self, keyword: str, db_session) -> None:
        """
        Add a keyword to the keywords list.
        
        Args:
            keyword: Keyword to add
            db_session: Database session for committing changes
        """
        if not self.keywords:
            self.keywords = []
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            db_session.commit()
    
    def set_embedding(self, embedding_vector: list, db_session) -> None:
        """
        Set the embedding vector for this chunk.
        
        Args:
            embedding_vector: List of floats representing the embedding (typically 3072-dim)
            db_session: Database session for committing changes
        """
        self.embedding = embedding_vector
        db_session.commit()
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<LegalDocumentChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index}, has_embedding={bool(self.embedding)})>"
