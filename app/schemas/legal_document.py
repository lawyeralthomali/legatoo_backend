"""
Legal Document schemas for FastAPI
Converted from Django forms
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class DocumentTypeEnum(str, Enum):
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


class LanguageEnum(str, Enum):
    """Language enumeration"""
    ARABIC = "ar"
    ENGLISH = "en"
    FRENCH = "fr"


class ProcessingStatusEnum(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class LegalDocumentBase(BaseModel):
    """Base legal document schema"""
    title: str = Field(..., min_length=1, max_length=255)
    document_type: DocumentTypeEnum = Field(default=DocumentTypeEnum.OTHER)
    language: LanguageEnum = Field(default=LanguageEnum.ARABIC)
    notes: Optional[str] = Field(None, max_length=1000)


class LegalDocumentCreate(LegalDocumentBase):
    """Schema for creating a legal document"""
    pass


class LegalDocumentUpdate(BaseModel):
    """Schema for updating a legal document"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    document_type: Optional[DocumentTypeEnum] = None
    language: Optional[LanguageEnum] = None
    notes: Optional[str] = Field(None, max_length=1000)


class LegalDocumentChunkBase(BaseModel):
    """Base legal document chunk schema"""
    chunk_index: int = Field(..., ge=1)
    content: str = Field(..., min_length=1)
    article_number: Optional[str] = Field(None, max_length=50)
    section_title: Optional[str] = Field(None, max_length=255)
    keywords: Optional[List[str]] = Field(default_factory=list)
    embedding: Optional[List[float]] = Field(default_factory=list)


class LegalDocumentChunkCreate(LegalDocumentChunkBase):
    """Schema for creating a legal document chunk"""
    document_id: UUID


class LegalDocumentChunkResponse(LegalDocumentChunkBase):
    """Schema for legal document chunk response"""
    id: UUID
    document_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class LegalDocumentResponse(LegalDocumentBase):
    """Schema for legal document response"""
    id: UUID
    file_path: str
    uploaded_by_id: Optional[UUID]
    created_at: datetime
    is_processed: bool
    processing_status: ProcessingStatusEnum
    file_url: str
    chunks: Optional[List[LegalDocumentChunkResponse]] = []
    
    class Config:
        from_attributes = True


class LegalDocumentListResponse(BaseModel):
    """Schema for legal document list response"""
    documents: List[LegalDocumentResponse]
    total: int
    page: int
    size: int


class DocumentUploadRequest(BaseModel):
    """Schema for document upload request"""
    title: str = Field(..., min_length=1, max_length=255)
    document_type: DocumentTypeEnum = Field(default=DocumentTypeEnum.OTHER)
    language: LanguageEnum = Field(default=LanguageEnum.ARABIC)
    notes: Optional[str] = Field(None, max_length=1000)


class DocumentProcessResponse(BaseModel):
    """Schema for document processing response"""
    success: bool
    message: str
    chunks_count: Optional[int] = None
    error: Optional[str] = None


class DocumentSearchRequest(BaseModel):
    """Schema for document search request"""
    query: str = Field(..., min_length=1, max_length=500)
    document_type: Optional[DocumentTypeEnum] = None
    language: Optional[LanguageEnum] = None
    limit: int = Field(default=10, ge=1, le=100)


class DocumentSearchResponse(BaseModel):
    """Schema for document search response"""
    results: List[Dict[str, Any]]
    total: int
    query: str
