"""
Legal Document models for FastAPI
Converted from Django models
"""
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class DocumentTypeEnum(enum.Enum):
    """Document type enumeration"""
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
    """Language enumeration"""
    ARABIC = "ar"
    ENGLISH = "en"
    FRENCH = "fr"


class ProcessingStatusEnum(enum.Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class LegalDocument(Base):
    """Model for storing legal documents"""
    __tablename__ = "legal_documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("profiles.id"), nullable=True)
    document_type = Column(String(50), default="other", nullable=False)
    language = Column(String(10), default="ar", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_status = Column(String(20), default="pending", nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    uploaded_by = relationship("Profile", back_populates="uploaded_documents")
    chunks = relationship("LegalDocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    @property
    def file_url(self):
        """Return the URL for the file"""
        return f"/media/{self.file_path}"


class LegalDocumentChunk(Base):
    """Model for storing chunks of legal documents with embeddings"""
    __tablename__ = "legal_document_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    document_id = Column(Integer, ForeignKey("legal_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    article_number = Column(String(50), nullable=True)
    section_title = Column(String(255), nullable=True)
    keywords = Column(JSON, default=list, nullable=True)
    embedding = Column(JSON, default=list, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    document = relationship("LegalDocument", back_populates="chunks")
    
    def add_keyword(self, keyword: str, db_session):
        """Add a keyword to the keywords list"""
        if not self.keywords:
            self.keywords = []
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            db_session.commit()
    
    def set_embedding(self, embedding_vector: list, db_session):
        """Set the embedding vector for this chunk"""
        self.embedding = embedding_vector
        db_session.commit()
