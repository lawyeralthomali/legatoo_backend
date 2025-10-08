"""
Embedding Schemas - نماذج البيانات للـ embeddings API

Pydantic schemas for embedding service requests and responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class GenerateEmbeddingRequest(BaseModel):
    """Request to generate embeddings for a single chunk."""
    chunk_id: int = Field(..., description="ID of the chunk to process")
    overwrite: bool = Field(False, description="Overwrite existing embedding")


class BatchGenerateRequest(BaseModel):
    """Request to generate embeddings for multiple chunks."""
    chunk_ids: List[int] = Field(..., description="List of chunk IDs to process", min_items=1)
    overwrite: bool = Field(False, description="Overwrite existing embeddings")
    
    @validator('chunk_ids')
    def validate_chunk_ids(cls, v):
        if len(v) > 1000:
            raise ValueError("Cannot process more than 1000 chunks at once")
        return v


class DocumentEmbeddingRequest(BaseModel):
    """Request to generate embeddings for all chunks in a document."""
    overwrite: bool = Field(False, description="Overwrite existing embeddings")


class SimilaritySearchRequest(BaseModel):
    """Request to search for similar chunks."""
    query: str = Field(..., description="Search query text", min_length=3, max_length=2000)
    top_k: int = Field(10, description="Number of top results to return", ge=1, le=100)
    threshold: float = Field(0.7, description="Minimum similarity threshold", ge=0.0, le=1.0)
    
    # Optional filters
    document_id: Optional[int] = Field(None, description="Filter by document ID")
    case_id: Optional[int] = Field(None, description="Filter by case ID")
    law_source_id: Optional[int] = Field(None, description="Filter by law source ID")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class EmbeddingInfo(BaseModel):
    """Information about a single embedding."""
    chunk_id: int
    embedding_dimension: int
    processing_time: float
    success: bool
    error: Optional[str] = None


class ChunkSimilarity(BaseModel):
    """Similar chunk result with similarity score."""
    chunk_id: int
    content: str
    similarity: float
    document_id: int
    chunk_index: int
    law_source_id: Optional[int] = None
    case_id: Optional[int] = None
    article_id: Optional[int] = None
    tokens_count: Optional[int] = None


class SimilaritySearchResponse(BaseModel):
    """Response for similarity search."""
    query: str
    results: List[ChunkSimilarity]
    total_results: int
    threshold: float
    processing_time: Optional[float] = None


class EmbeddingStatus(BaseModel):
    """Embedding status for a document or globally."""
    total_chunks: int
    chunks_with_embeddings: int
    chunks_without_embeddings: int
    completion_percentage: float
    status: str  # 'complete', 'partial', 'not_started'


class DocumentEmbeddingStatus(EmbeddingStatus):
    """Embedding status for a specific document."""
    document_id: int


class GlobalEmbeddingStatus(EmbeddingStatus):
    """Global embedding status for the entire system."""
    model_name: str
    device: str


class ProcessingStatistics(BaseModel):
    """Statistics from embedding generation process."""
    total_chunks: int
    processed_chunks: int
    failed_chunks: int
    processing_time: str
    success: bool
    error: Optional[str] = None


class DocumentProcessingResponse(ProcessingStatistics):
    """Response for document embedding generation."""
    document_id: int


class BatchProcessingResponse(ProcessingStatistics):
    """Response for batch embedding generation."""
    pass


class EmbeddingModelInfo(BaseModel):
    """Information about the embedding model."""
    model_name: str
    model_path: str
    embedding_dimension: int
    device: str
    max_seq_length: int
    batch_size: int
