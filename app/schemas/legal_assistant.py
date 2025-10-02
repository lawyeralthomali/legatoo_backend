"""
Legal Assistant schemas for request/response validation.

This module defines Pydantic models for legal document operations,
ensuring consistent validation and serialization across the API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from enum import Enum
from ..utils.arabic_text_processor import ArabicTextProcessor


class DocumentTypeEnum(str, Enum):
    """Document type enumeration for legal documents."""
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
    """Language enumeration for documents."""
    ARABIC = "ar"
    ENGLISH = "en"
    FRENCH = "fr"


class ProcessingStatusEnum(str, Enum):
    """Processing status for document processing pipeline."""
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    document_type: DocumentTypeEnum = Field(default=DocumentTypeEnum.OTHER, description="Type of legal document")
    language: LanguageEnum = Field(default=LanguageEnum.ARABIC, description="Document language")
    notes: Optional[str] = Field(None, description="Additional notes about the document")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Saudi Labor Law 2023",
                "document_type": "labor_law",
                "language": "ar",
                "notes": "Updated labor law regulations"
            }
        }


class DocumentChunkResponse(BaseModel):
    """Response model for a document chunk with RTL support."""
    id: int = Field(..., description="Chunk ID")
    chunk_index: int = Field(..., description="Index of the chunk in the document")
    content: str = Field(..., description="Text content of the chunk")
    article_number: Optional[str] = Field(None, description="Article number if detected")
    section_title: Optional[str] = Field(None, description="Section title if detected")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    similarity_score: Optional[float] = Field(None, description="Similarity score (for search results)")
    
    # RTL and formatting fields
    is_rtl: bool = Field(default=False, description="Whether text is right-to-left (Arabic)")
    text_direction: str = Field(default="ltr", description="Text direction: 'rtl' or 'ltr'")
    formatted_content: Optional[str] = Field(None, description="HTML formatted content with proper direction")
    normalized_content: Optional[str] = Field(None, description="Normalized text content")
    
    @field_validator('content', mode='before')
    @classmethod
    def process_content(cls, v):
        """Process content for RTL handling and normalization."""
        try:
            if not v:
                return v
            
            # Get language from document if available
            language = "ar"  # Default to Arabic for legal documents
            
            # Process Arabic text
            processed = ArabicTextProcessor.format_arabic_chunk(v, language)
            
            # Store processed data in a way that can be accessed by other validators
            # In Pydantic v2, we need to use model_validator for cross-field validation
            return processed['content']
        except Exception as e:
            # Log error and return original content
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in content validator: {e}")
            return v
    
    @field_validator('keywords', mode='before')
    @classmethod
    def process_keywords(cls, v):
        """Process keywords for Arabic text."""
        if not v:
            return v
        
        # For now, just return the keywords as-is
        # We'll handle Arabic keyword enhancement in a model_validator
        return v
    
    @model_validator(mode='after')
    def process_rtl_fields(self):
        """Process RTL fields after all field validation is complete."""
        try:
            if not self.content:
                return self
            
            # Process Arabic text
            processed = ArabicTextProcessor.format_arabic_chunk(self.content, "ar")
            
            # Set RTL fields
            self.is_rtl = processed['is_rtl']
            self.text_direction = processed['language'] if processed['is_rtl'] else 'ltr'
            self.formatted_content = processed['formatted_content']
            self.normalized_content = processed['content']
            
            # Enhance keywords if Arabic
            if processed['is_rtl'] and self.content:
                arabic_keywords = ArabicTextProcessor.extract_arabic_keywords(self.content)
                # Merge with existing keywords, removing duplicates
                existing_keywords = self.keywords or []
                all_keywords = list(dict.fromkeys(existing_keywords + arabic_keywords))
                self.keywords = all_keywords[:15]  # Limit to 15 keywords
            
            return self
        except Exception as e:
            # Log error and return self unchanged
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in RTL processing: {e}")
            return self

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Response model for legal document."""
    id: int = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    file_path: str = Field(..., description="Path to the uploaded file")
    file_url: Optional[str] = Field(None, description="URL to access the file")
    document_type: str = Field(..., description="Type of document")
    language: str = Field(..., description="Document language")
    processing_status: str = Field(..., description="Current processing status")
    is_processed: bool = Field(..., description="Whether processing is complete")
    notes: Optional[str] = Field(None, description="Additional notes")
    chunks_count: Optional[int] = Field(None, description="Number of chunks created")
    created_at: datetime = Field(..., description="Creation timestamp")
    uploaded_by_id: Optional[int] = Field(None, description="ID of the user who uploaded")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


class SearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query in Arabic or English")
    document_type: Optional[DocumentTypeEnum] = Field(None, description="Filter by document type")
    language: Optional[LanguageEnum] = Field(None, description="Filter by language")
    article_number: Optional[str] = Field(None, description="Filter by specific article number")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "ما هي حقوق العامل في الإجازات السنوية؟",
                "document_type": "labor_law",
                "language": "ar",
                "limit": 5,
                "similarity_threshold": 0.7
            }
        }


class SearchResult(BaseModel):
    """Single search result with document context."""
    chunk: DocumentChunkResponse = Field(..., description="Matching chunk")
    document: DocumentResponse = Field(..., description="Source document")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    highlights: List[str] = Field(default_factory=list, description="Highlighted matching phrases")


class SearchResponse(BaseModel):
    """Response model for search results."""
    results: List[SearchResult] = Field(..., description="List of search results")
    total_found: int = Field(..., description="Total number of results found")
    query_time_ms: float = Field(..., description="Query execution time in milliseconds")
    query: str = Field(..., description="Original search query")


class DocumentUpdateRequest(BaseModel):
    """Request model for updating document metadata."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated title")
    document_type: Optional[DocumentTypeEnum] = Field(None, description="Updated document type")
    language: Optional[LanguageEnum] = Field(None, description="Updated language")
    notes: Optional[str] = Field(None, description="Updated notes")


class ProcessingProgressResponse(BaseModel):
    """Response model for document processing progress."""
    document_id: int = Field(..., description="Document ID")
    status: ProcessingStatusEnum = Field(..., description="Current processing status")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Processing progress (0-100)")
    chunks_processed: int = Field(default=0, description="Number of chunks processed")
    total_chunks: int = Field(default=0, description="Total chunks to process")
    message: str = Field(..., description="Status message")
    error: Optional[str] = Field(None, description="Error message if processing failed")


class DocumentStatsResponse(BaseModel):
    """Response model for document statistics."""
    total_documents: int = Field(..., description="Total number of documents")
    total_chunks: int = Field(..., description="Total number of chunks")
    documents_by_type: Dict[str, int] = Field(..., description="Count of documents by type")
    documents_by_language: Dict[str, int] = Field(..., description="Count of documents by language")
    processing_pending: int = Field(default=0, description="Number of pending documents")
    processing_done: int = Field(default=0, description="Number of processed documents")
    processing_error: int = Field(default=0, description="Number of failed documents")


class ChunkDetailResponse(BaseModel):
    """Detailed response for a single chunk."""
    chunk: DocumentChunkResponse = Field(..., description="Chunk information")
    document: DocumentResponse = Field(..., description="Parent document information")
    previous_chunk_id: Optional[int] = Field(None, description="ID of previous chunk")
    next_chunk_id: Optional[int] = Field(None, description="ID of next chunk")
