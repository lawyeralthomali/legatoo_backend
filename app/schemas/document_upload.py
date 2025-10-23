"""
Document Upload Schemas for Legal Knowledge Management

This module defines Pydantic schemas for document upload operations,
including request validation and response formatting.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class DocumentUploadRequest(BaseModel):
    """Request schema for document upload with metadata."""
    
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    category: str = Field(..., description="Document category")
    uploaded_by: Optional[int] = Field(None, description="User ID who uploaded the document")
    
    @validator('category')
    def validate_category(cls, v):
        """Validate document category."""
        allowed_categories = ['law', 'article', 'manual', 'policy', 'contract']
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {", ".join(allowed_categories)}')
        return v


class LawSourceSummary(BaseModel):
    """Summary of a law source created/updated during upload."""
    
    id: int
    name: str
    type: str
    jurisdiction: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[str] = None
    articles_count: int = 0


class LawArticleSummary(BaseModel):
    """Summary of law articles created during upload."""
    
    id: int
    article_number: Optional[str] = None
    title: Optional[str] = None
    order_index: int = 0


class KnowledgeChunkSummary(BaseModel):
    """Summary of knowledge chunks created during upload."""
    
    id: int
    chunk_index: int
    tokens_count: Optional[int] = None
    law_source_id: Optional[int] = None
    article_id: Optional[int] = None


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload operation."""
    
    # Document information
    document_id: int
    title: str
    category: str
    file_path: str
    file_hash: str
    status: str
    uploaded_at: datetime
    
    # Processing summary
    chunks_created: int
    law_sources_processed: int
    articles_processed: int
    
    # Detailed summaries
    law_sources: List[LawSourceSummary] = []
    articles: List[LawArticleSummary] = []
    chunks: List[KnowledgeChunkSummary] = []
    
    # Processing metadata
    processing_time_seconds: float
    file_size_bytes: int
    duplicate_detected: bool = False


class DocumentUploadError(BaseModel):
    """Error details for document upload failures."""
    
    error_type: str
    error_message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class BulkOperationResult(BaseModel):
    """Result of bulk database operations."""
    
    operation_type: str
    records_processed: int
    records_created: int
    records_updated: int
    records_skipped: int
    errors: List[str] = []


class DocumentProcessingStats(BaseModel):
    """Statistics for document processing operations."""
    
    total_processing_time: float
    file_parsing_time: float
    database_operations_time: float
    chunk_creation_time: float
    memory_usage_mb: Optional[float] = None
    peak_memory_mb: Optional[float] = None
