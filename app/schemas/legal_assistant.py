"""
Legal Assistant schemas for FastAPI
Converted from Django views
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ChatMessage(BaseModel):
    """Schema for chat message"""
    content: str = Field(..., min_length=1, max_length=2000)
    isUser: bool = Field(default=True)
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Schema for chat request"""
    question: str = Field(..., min_length=1, max_length=1000)
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Schema for chat response"""
    answer: str
    chunks_used: int
    tokens_used: int
    language: str
    quality_score: str
    sources: List[str]
    has_context: bool


class DocumentSummaryRequest(BaseModel):
    """Schema for document summary request"""
    document_id: str


class DocumentSummaryResponse(BaseModel):
    """Schema for document summary response"""
    title: str
    summary: str
    chunk_count: int
    total_length: int


class KeywordSearchRequest(BaseModel):
    """Schema for keyword search request"""
    keywords: List[str] = Field(..., min_items=1, max_items=10)
    limit: int = Field(default=10, ge=1, le=50)


class KeywordSearchResponse(BaseModel):
    """Schema for keyword search response"""
    results: List[Dict[str, Any]]
    total: int
    keywords: List[str]


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    success: bool
    message: str
    filename: Optional[str] = None


class LanguageDetectionRequest(BaseModel):
    """Schema for language detection request"""
    text: str = Field(..., min_length=1, max_length=1000)


class LanguageDetectionResponse(BaseModel):
    """Schema for language detection response"""
    language: str
    confidence: float
    arabic_chars: int
    english_chars: int
    total_chars: int


class AssistantStatusResponse(BaseModel):
    """Schema for assistant status response"""
    status: str
    dependencies: Dict[str, bool]
    features_available: List[str]
    models_available: List[str]


class ConversationHistory(BaseModel):
    """Schema for conversation history"""
    messages: List[ChatMessage]
    session_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AssistantConfig(BaseModel):
    """Schema for assistant configuration"""
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1500, ge=100, le=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    max_context_tokens: int = Field(default=8000, ge=1000, le=16000)
