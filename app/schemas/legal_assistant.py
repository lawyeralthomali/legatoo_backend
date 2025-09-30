"""
Legal Assistant schemas for FastAPI
Minimized version with only essential schemas
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
