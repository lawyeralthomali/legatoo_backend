"""
Analysis Schemas - نماذج البيانات لنظام التحليل القانوني

Pydantic schemas for legal analysis requests and responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


# ==================== REQUEST SCHEMAS ====================

class AnalysisRequest(BaseModel):
    """Request schema for legal analysis."""
    case_text: str = Field(..., description="نص القضية للتحليل", min_length=10, max_length=10000)
    validation_level: Optional[str] = Field("standard", description="مستوى التحقق (quick, standard, deep)")
    
    @validator('case_text')
    def validate_case_text(cls, v):
        if not v.strip():
            raise ValueError("Case text cannot be empty")
        return v.strip()
    
    @validator('validation_level')
    def validate_validation_level(cls, v):
        if v not in ['quick', 'standard', 'deep']:
            raise ValueError("Validation level must be: quick, standard, or deep")
        return v


class RAGAnalysisRequest(BaseModel):
    """Request schema for RAG analysis."""
    case_text: str = Field(..., description="نص القضية للتحليل", min_length=10, max_length=10000)
    max_laws: int = Field(5, description="عدد القوانين المسترجعة", ge=1, le=10)
    max_cases: int = Field(3, description="عدد القضايا المشابهة", ge=1, le=10)
    include_principles: bool = Field(True, description="تضمين المبادئ القانونية")
    
    @validator('case_text')
    def validate_case_text(cls, v):
        if not v.strip():
            raise ValueError("Case text cannot be empty")
        return v.strip()


class QuickAnalysisRequest(BaseModel):
    """Request schema for quick analysis."""
    case_text: str = Field(..., description="نص القضية", min_length=10, max_length=5000)
    
    @validator('case_text')
    def validate_case_text(cls, v):
        if not v.strip():
            raise ValueError("Case text cannot be empty")
        return v.strip()


class ClassificationRequest(BaseModel):
    """Request schema for case classification."""
    case_text: str = Field(..., description="نص القضية للتصنيف", min_length=10, max_length=5000)
    
    @validator('case_text')
    def validate_case_text(cls, v):
        if not v.strip():
            raise ValueError("Case text cannot be empty")
        return v.strip()


class EntityExtractionRequest(BaseModel):
    """Request schema for legal entity extraction."""
    case_text: str = Field(..., description="نص القضية لاستخراج الكيانات", min_length=10, max_length=5000)
    
    @validator('case_text')
    def validate_case_text(cls, v):
        if not v.strip():
            raise ValueError("Case text cannot be empty")
        return v.strip()


class LegalQuestionRequest(BaseModel):
    """Request schema for legal question answering."""
    question: str = Field(..., description="السؤال القانوني", min_length=5, max_length=1000)
    context_type: Optional[str] = Field("both", description="نوع السياق (laws, cases, both)")
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()
    
    @validator('context_type')
    def validate_context_type(cls, v):
        if v not in ['laws', 'cases', 'both']:
            raise ValueError("Context type must be: laws, cases, or both")
        return v


class StrategyGenerationRequest(BaseModel):
    """Request schema for legal strategy generation."""
    case_analysis: Dict[str, Any] = Field(..., description="تحليل القضية السابق")


# ==================== RESPONSE SCHEMAS ====================

class ClassificationResponse(BaseModel):
    """Response schema for case classification."""
    case_type: str
    complexity: str
    confidence: float
    key_issue: Optional[str] = None


class LegalAnalysisResponse(BaseModel):
    """Response schema for legal analysis."""
    facts: Optional[str] = None
    rights_obligations: Optional[str] = None
    evidence: Optional[List[str]] = None
    required_procedures: Optional[List[str]] = None


class ApplicableLaw(BaseModel):
    """Schema for applicable law information."""
    law_name: str
    article_numbers: Optional[List[str]] = None
    applicability: Optional[str] = None
    conditions: Optional[str] = None


class GapsOpportunities(BaseModel):
    """Schema for legal gaps and opportunities."""
    procedural_gaps: Optional[List[str]] = None
    opponent_weaknesses: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None
    risks: Optional[List[str]] = None


class StrategicPlan(BaseModel):
    """Schema for strategic plan."""
    urgent_24h: Optional[List[str]] = None
    short_term_week: Optional[List[str]] = None
    medium_term_month: Optional[List[str]] = None
    negotiation_tips: Optional[List[str]] = None


class OutcomeAssessment(BaseModel):
    """Schema for outcome assessment."""
    best_case: Optional[str] = None
    expected_case: Optional[str] = None
    worst_case: Optional[str] = None
    recommendation: Optional[str] = None


class ComprehensiveAnalysis(BaseModel):
    """Schema for comprehensive analysis result."""
    classification: Optional[Dict[str, Any]] = None
    legal_analysis: Optional[Dict[str, Any]] = None
    applicable_laws: Optional[List[Dict[str, Any]]] = None
    gaps_opportunities: Optional[Dict[str, Any]] = None
    strategic_plan: Optional[Dict[str, Any]] = None
    outcome_assessment: Optional[Dict[str, Any]] = None
    raw_analysis: Optional[str] = None
    parsed: Optional[bool] = True


class ValidationResults(BaseModel):
    """Schema for validation results."""
    laws_validation: Dict[str, Any]
    cases_validation: Dict[str, Any]
    overall_confidence: float
    recommendations: List[str]


class HybridAnalysisResponse(BaseModel):
    """Response schema for hybrid analysis."""
    success: bool
    analysis_source: str = "hybrid"
    gemini_analysis: Dict[str, Any]
    validation: ValidationResults
    overall_confidence: float
    recommendations: List[str]
    quality_score: Optional[str] = None
    additional_laws: Optional[List[Dict]] = None
    processing_time_seconds: Optional[float] = None
    timestamp: Optional[str] = None


class RAGSource(BaseModel):
    """Schema for RAG source."""
    content: str
    similarity: float
    source: Optional[str] = None
    article: Optional[str] = None
    verified: Optional[bool] = False


class CaseSource(BaseModel):
    """Schema for case source."""
    content: str
    similarity: float
    case_number: Optional[str] = None
    court: Optional[str] = None
    decision_date: Optional[str] = None


class RAGSources(BaseModel):
    """Schema for RAG sources."""
    laws: List[RAGSource]
    cases: List[CaseSource]
    principles: List[str]
    procedural_rules: List[str]


class RAGMetadata(BaseModel):
    """Schema for RAG metadata."""
    sources_count: int
    laws_used: int
    cases_used: int
    context_provided: Optional[Dict] = None


class QualityIndicators(BaseModel):
    """Schema for quality indicators."""
    grounded_in_sources: bool
    traceable: bool
    verified_laws_used: int


class RAGAnalysisResponse(BaseModel):
    """Response schema for RAG analysis."""
    success: bool
    analysis: Dict[str, Any]
    sources: RAGSources
    metadata: RAGMetadata
    quality_indicators: QualityIndicators
    processing_time_seconds: Optional[float] = None
    timestamp: Optional[str] = None
    analysis_type: str = "rag"


class QuickAnalysisResponse(BaseModel):
    """Response schema for quick analysis."""
    success: bool
    analysis_type: str = "quick"
    classification: Dict[str, Any]
    similar_cases_count: int
    recommendation: str


class LegalEntities(BaseModel):
    """Schema for extracted legal entities."""
    parties: List[str]
    dates: List[str]
    amounts: List[str]
    locations: List[str]
    documents: List[str]
    laws_mentioned: List[str]


class EntityExtractionResponse(BaseModel):
    """Response schema for entity extraction."""
    success: bool
    entities: LegalEntities
    validated_laws: Optional[Dict[str, Any]] = None


class LegalStrategy(BaseModel):
    """Schema for legal strategy."""
    immediate_actions: List[str]
    documents_needed: List[str]
    witnesses_to_contact: List[str]
    legal_arguments: List[str]
    negotiation_strategy: str
    litigation_strategy: str
    settlement_options: List[str]
    estimated_timeline: str
    estimated_costs: str
    success_probability: float


class StrategyResponse(BaseModel):
    """Response schema for strategy generation."""
    success: bool
    strategy: LegalStrategy


class LegalAnswer(BaseModel):
    """Schema for legal question answer."""
    success: bool
    question: str
    answer: str
    sources: Dict[str, List]


class AnalysisMetadata(BaseModel):
    """Metadata for analysis results."""
    model: str = "gemini-pro"
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None
    timestamp: str


# ==================== STATUS SCHEMAS ====================

class AnalysisStatus(BaseModel):
    """Schema for analysis system status."""
    gemini_enabled: bool
    search_service_available: bool
    total_laws_in_db: int
    total_cases_in_db: int
    rag_ready: bool
