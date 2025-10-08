"""
Search Schemas - نماذج البيانات لنظام البحث الدلالي

Pydantic schemas for semantic search requests and responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ==================== REQUEST SCHEMAS ====================

class SimilarSearchRequest(BaseModel):
    """Request schema for similar document search."""
    query: str = Field(..., description="Search query text", min_length=3, max_length=2000)
    top_k: int = Field(10, description="Number of top results", ge=1, le=100)
    threshold: float = Field(0.7, description="Minimum similarity threshold", ge=0.0, le=1.0)
    
    # Optional filters
    jurisdiction: Optional[str] = Field(None, description="Filter by jurisdiction")
    law_source_id: Optional[int] = Field(None, description="Filter by law source ID")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class SimilarCasesRequest(BaseModel):
    """Request schema for similar cases search."""
    query: str = Field(..., description="Search query text", min_length=3, max_length=2000)
    top_k: int = Field(10, description="Number of top results", ge=1, le=100)
    threshold: float = Field(0.7, description="Minimum similarity threshold", ge=0.0, le=1.0)
    
    # Optional filters
    jurisdiction: Optional[str] = Field(None, description="Filter by jurisdiction")
    case_type: Optional[str] = Field(None, description="Filter by case type")
    court_level: Optional[str] = Field(None, description="Filter by court level")
    case_id: Optional[int] = Field(None, description="Filter by specific case ID")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
    
    @validator('case_type')
    def validate_case_type(cls, v):
        if v is not None:
            valid_types = ['مدني', 'جنائي', 'تجاري', 'عمل', 'إداري']
            if v not in valid_types:
                raise ValueError(f"Case type must be one of: {', '.join(valid_types)}")
        return v
    
    @validator('court_level')
    def validate_court_level(cls, v):
        if v is not None:
            valid_levels = ['ابتدائي', 'استئناف', 'تمييز', 'عالي']
            if v not in valid_levels:
                raise ValueError(f"Court level must be one of: {', '.join(valid_levels)}")
        return v


class HybridSearchRequest(BaseModel):
    """Request schema for hybrid search across multiple document types."""
    query: str = Field(..., description="Search query text", min_length=3, max_length=2000)
    search_types: List[str] = Field(['laws', 'cases'], description="Types to search")
    top_k: int = Field(5, description="Results per type", ge=1, le=50)
    threshold: float = Field(0.6, description="Minimum similarity threshold", ge=0.0, le=1.0)
    
    # Optional filters
    jurisdiction: Optional[str] = Field(None, description="Filter by jurisdiction")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
    
    @validator('search_types')
    def validate_search_types(cls, v):
        valid_types = ['laws', 'cases', 'all']
        for search_type in v:
            if search_type not in valid_types:
                raise ValueError(f"Search type must be one of: {', '.join(valid_types)}")
        return v


class SearchSuggestionsRequest(BaseModel):
    """Request schema for search suggestions."""
    partial_query: str = Field(..., description="Partial search query", min_length=1, max_length=100)
    limit: int = Field(5, description="Maximum suggestions", ge=1, le=20)


# ==================== RESPONSE SCHEMAS ====================

class LawMetadata(BaseModel):
    """Metadata for law search result."""
    law_id: int
    law_name: str
    law_type: str
    jurisdiction: Optional[str] = None
    issue_date: Optional[str] = None


class ArticleMetadata(BaseModel):
    """Metadata for law article."""
    article_id: int
    article_number: Optional[str] = None
    title: Optional[str] = None
    keywords: Optional[List[str]] = None


class BranchMetadata(BaseModel):
    """Metadata for law branch."""
    branch_id: int
    branch_number: Optional[str] = None
    branch_name: str


class ChapterMetadata(BaseModel):
    """Metadata for law chapter."""
    chapter_id: int
    chapter_number: Optional[str] = None
    chapter_name: str


class CaseMetadata(BaseModel):
    """Metadata for legal case."""
    case_id: int
    case_number: Optional[str] = None
    title: str
    jurisdiction: Optional[str] = None
    court_name: Optional[str] = None
    decision_date: Optional[str] = None
    case_type: Optional[str] = None
    court_level: Optional[str] = None
    status: Optional[str] = None


class SearchResult(BaseModel):
    """Base search result schema."""
    chunk_id: int
    content: str
    similarity: float
    source_type: str  # 'law' or 'case'
    chunk_index: int
    tokens_count: Optional[int] = None
    verified: bool = False


class LawSearchResult(SearchResult):
    """Extended search result for law documents."""
    source_type: str = 'law'
    law_metadata: Optional[LawMetadata] = None
    article_metadata: Optional[ArticleMetadata] = None
    branch_metadata: Optional[BranchMetadata] = None
    chapter_metadata: Optional[ChapterMetadata] = None


class CaseSearchResult(SearchResult):
    """Extended search result for case documents."""
    source_type: str = 'case'
    case_metadata: Optional[CaseMetadata] = None


class SearchResultsResponse(BaseModel):
    """Response schema for search results."""
    query: str
    results: List[SearchResult]
    total_results: int
    threshold: float
    search_time: Optional[float] = None


class HybridSearchResults(BaseModel):
    """Response schema for hybrid search."""
    laws: Optional[Dict[str, Any]] = None
    cases: Optional[Dict[str, Any]] = None


class HybridSearchResponse(BaseModel):
    """Response schema for hybrid search."""
    query: str
    search_types: List[str]
    timestamp: str
    total_results: int
    laws: Optional[Dict[str, Any]] = None
    cases: Optional[Dict[str, Any]] = None


class SearchSuggestionsResponse(BaseModel):
    """Response schema for search suggestions."""
    partial_query: str
    suggestions: List[str]
    count: int


class SearchStatisticsResponse(BaseModel):
    """Response schema for search statistics."""
    total_searchable_chunks: int
    law_chunks: int
    case_chunks: int
    cache_size: int
    cache_enabled: bool


# ==================== UTILITY SCHEMAS ====================

class SearchFilter(BaseModel):
    """Utility schema for search filters."""
    jurisdiction: Optional[str] = None
    law_source_id: Optional[int] = None
    case_id: Optional[int] = None
    case_type: Optional[str] = None
    court_level: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class RankingOptions(BaseModel):
    """Options for result ranking."""
    use_recency_boost: bool = False
    use_verification_boost: bool = True
    custom_boost_factors: Optional[Dict[str, float]] = None
