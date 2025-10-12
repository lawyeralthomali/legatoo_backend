"""
Analysis Router - API endpoints for AI-powered legal analysis

Provides REST API endpoints for comprehensive legal analysis using Gemini AI,
hybrid analysis, and RAG (Retrieval-Augmented Generation).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal.analysis.gemini_legal_analyzer import GeminiLegalAnalyzer
from ..services.legal.analysis.hybrid_analysis_service import HybridAnalysisService
from ..services.legal.analysis.legal_rag_service import LegalRAGService
from ..utils.auth import get_current_user
from ..schemas.profile_schemas import TokenData
from ..schemas.analysis import (
    AnalysisRequest,
    RAGAnalysisRequest,
    QuickAnalysisRequest,
    ClassificationRequest,
    EntityExtractionRequest,
    LegalQuestionRequest,
    StrategyGenerationRequest
)
from ..schemas.response import ApiResponse, create_success_response, create_error_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["Legal Analysis - AI-Powered"]
)


@router.get("/status", response_model=ApiResponse)
async def get_analysis_status(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    الحصول على حالة نظام التحليل القانوني.
    
    **Analysis System Status**:
    - Check if Gemini AI is enabled
    - Check semantic search availability
    - Get knowledge base statistics
    - Check RAG readiness
    
    **Example**:
    ```
    GET /api/v1/analysis/status
    ```
    
    **Response**:
    ```json
    {
      "success": true,
      "message": "Analysis system status",
      "data": {
        "gemini_enabled": true,
        "search_service_available": true,
        "total_laws_in_db": 600,
        "total_cases_in_db": 218,
        "rag_ready": true
      }
    }
    ```
    """
    try:
        logger.info(f"📊 Getting analysis system status for user {current_user.sub}")
        
        # Initialize services
        gemini = GeminiLegalAnalyzer()
        hybrid_service = HybridAnalysisService(db)
        
        # Get stats from search service
        stats = await hybrid_service.search_service.get_search_statistics()
        
        status_data = {
            "gemini_enabled": gemini.is_enabled(),
            "search_service_available": True,
            "total_laws_in_db": stats.get('law_chunks', 0),
            "total_cases_in_db": stats.get('case_chunks', 0),
            "rag_ready": gemini.is_enabled() and stats.get('total_searchable_chunks', 0) > 0
        }
        
        return create_success_response(
            message="Analysis system status",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get status: {str(e)}")
        return create_error_response(message=f"Failed to get status: {str(e)}")


@router.post("/comprehensive", response_model=ApiResponse)
async def comprehensive_analysis(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    تحليل قانوني شامل باستخدام Gemini AI فقط.
    
    **Comprehensive Legal Analysis**:
    - Uses Gemini AI for deep legal understanding
    - Provides classification, analysis, and strategy
    - No validation against knowledge base
    - Fastest option for initial analysis
    
    **Request Body**:
    ```json
    {
      "case_text": "نص القضية هنا...",
      "validation_level": "standard"
    }
    ```
    
    **Response includes**:
    - Case classification
    - Legal analysis
    - Applicable laws
    - Strategic recommendations
    - Risk assessment
    
    **Example**:
    ```
    POST /api/v1/analysis/comprehensive
    ```
    """
    try:
        logger.info(f"🔍 Comprehensive analysis for user {current_user.sub}")
        logger.info(f"📝 Case text length: {len(request.case_text)} characters")
        
        # Initialize Gemini analyzer
        gemini = GeminiLegalAnalyzer()
        
        if not gemini.is_enabled():
            return create_error_response(
                message="Gemini AI is not configured. Please set GOOGLE_AI_API_KEY environment variable."
            )
        
        # Perform analysis
        result = await gemini.comprehensive_legal_analysis(request.case_text)
        
        if not result.get('success'):
            return create_error_response(
                message=f"Analysis failed: {result.get('error', 'Unknown error')}"
            )
        
        return create_success_response(
            message="Comprehensive analysis completed",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Comprehensive analysis failed: {str(e)}")
        return create_error_response(message=f"Analysis failed: {str(e)}")


@router.post("/hybrid", response_model=ApiResponse)
async def hybrid_analysis(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    تحليل هجين - يجمع بين Gemini AI والبحث الدلالي للتحقق.
    
    **Hybrid Analysis (Recommended)**:
    - Combines Gemini AI analysis with semantic search validation
    - Validates laws and regulations against knowledge base
    - Finds similar cases for precedents
    - Provides confidence scores
    - Best balance between speed and accuracy
    
    **Validation Levels**:
    - `quick`: Fast validation (1-2 seconds)
    - `standard`: Balanced validation (2-4 seconds) - Recommended
    - `deep`: Thorough validation (4-6 seconds)
    
    **Request Body**:
    ```json
    {
      "case_text": "نص القضية هنا...",
      "validation_level": "standard"
    }
    ```
    
    **Response includes**:
    - Gemini analysis
    - Validation results
    - Confidence score
    - Recommendations
    - Quality indicators
    
    **Example**:
    ```
    POST /api/v1/analysis/hybrid
    ```
    """
    try:
        logger.info(f"🔍 Hybrid analysis for user {current_user.sub}")
        logger.info(f"📝 Case text: '{request.case_text[:100]}...'")
        logger.info(f"⚙️ Validation level: {request.validation_level}")
        
        # Initialize hybrid service
        hybrid_service = HybridAnalysisService(db)
        
        # Perform hybrid analysis
        result = await hybrid_service.analyze_case(
            case_text=request.case_text,
            validation_level=request.validation_level
        )
        
        if not result.get('success'):
            return create_error_response(
                message=f"Hybrid analysis failed: {result.get('error', 'Unknown error')}"
            )
        
        return create_success_response(
            message=f"Hybrid analysis completed with {result.get('overall_confidence', 0):.1f}% confidence",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Hybrid analysis failed: {str(e)}")
        return create_error_response(message=f"Analysis failed: {str(e)}")


@router.post("/rag", response_model=ApiResponse)
async def rag_analysis(
    request: RAGAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    تحليل RAG المتقدم - أعلى دقة ممكنة.
    
    **RAG Analysis (Maximum Accuracy)**:
    - Retrieves relevant laws and cases from knowledge base
    - Augments Gemini's prompt with this context
    - Generates analysis grounded in actual sources
    - Provides full traceability
    - Highest quality for critical cases
    
    **Features**:
    - Sources are included in response
    - All claims are traceable
    - Reduced AI hallucinations
    - Precedent-based recommendations
    
    **Request Body**:
    ```json
    {
      "case_text": "نص القضية هنا...",
      "max_laws": 5,
      "max_cases": 3,
      "include_principles": true
    }
    ```
    
    **Parameters**:
    - `max_laws`: Number of laws to retrieve (1-10)
    - `max_cases`: Number of cases to retrieve (1-10)
    - `include_principles`: Include legal principles
    
    **Response includes**:
    - Analysis with sources
    - Retrieved laws
    - Similar cases
    - Legal principles
    - Quality indicators
    
    **Example**:
    ```
    POST /api/v1/analysis/rag
    ```
    """
    try:
        logger.info(f"🔍 RAG analysis for user {current_user.sub}")
        logger.info(f"📝 Case text: '{request.case_text[:100]}...'")
        logger.info(f"⚙️ Parameters: max_laws={request.max_laws}, max_cases={request.max_cases}")
        
        # Initialize RAG service
        rag_service = LegalRAGService(db)
        
        # Perform RAG analysis
        result = await rag_service.rag_analysis(
            case_text=request.case_text,
            max_laws=request.max_laws,
            max_cases=request.max_cases,
            include_principles=request.include_principles
        )
        
        if not result.get('success'):
            return create_error_response(
                message=f"RAG analysis failed: {result.get('error', 'Unknown error')}"
            )
        
        sources_count = result.get('metadata', {}).get('sources_count', 0)
        
        return create_success_response(
            message=f"RAG analysis completed using {sources_count} sources",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ RAG analysis failed: {str(e)}")
        return create_error_response(message=f"Analysis failed: {str(e)}")


@router.post("/quick", response_model=ApiResponse)
async def quick_analysis(
    request: QuickAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    تحليل سريع للقضية (للحالات العاجلة).
    
    **Quick Analysis**:
    - Fast case classification
    - Basic case type and complexity
    - Quick similarity search
    - Recommended for urgent triage
    - Response time: < 2 seconds
    
    **Use cases**:
    - Initial case triage
    - Urgent consultations
    - Quick assessments
    - Batch processing
    
    **Request Body**:
    ```json
    {
      "case_text": "نص القضية هنا..."
    }
    ```
    
    **Response includes**:
    - Case classification
    - Case type and complexity
    - Similar cases count
    - Recommendation for next steps
    
    **Example**:
    ```
    POST /api/v1/analysis/quick
    ```
    """
    try:
        logger.info(f"⚡ Quick analysis for user {current_user.sub}")
        
        # Initialize hybrid service
        hybrid_service = HybridAnalysisService(db)
        
        # Perform quick analysis
        result = await hybrid_service.quick_analysis(request.case_text)
        
        if not result.get('success'):
            return create_error_response(
                message=f"Quick analysis failed: {result.get('error', 'Unknown error')}"
            )
        
        return create_success_response(
            message="Quick analysis completed",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Quick analysis failed: {str(e)}")
        return create_error_response(message=f"Analysis failed: {str(e)}")


@router.post("/classify", response_model=ApiResponse)
async def classify_case(
    request: ClassificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    تصنيف القضية فقط (بدون تحليل كامل).
    
    **Case Classification Only**:
    - Determines case type
    - Assesses complexity
    - Provides confidence score
    - Identifies key issue
    - Lightweight and fast
    
    **Classifications**:
    - **Type**: مدني, جنائي, عمل, تجاري, إداري, أحوال شخصية
    - **Complexity**: بسيطة, متوسطة, معقدة
    - **Confidence**: 0-100%
    
    **Request Body**:
    ```json
    {
      "case_text": "نص القضية هنا..."
    }
    ```
    
    **Example**:
    ```
    POST /api/v1/analysis/classify
    ```
    """
    try:
        logger.info(f"🏷️ Classifying case for user {current_user.sub}")
        
        # Initialize Gemini
        gemini = GeminiLegalAnalyzer()
        
        if not gemini.is_enabled():
            return create_error_response(message="Gemini AI is not enabled")
        
        # Classify
        result = await gemini.quick_case_classification(request.case_text)
        
        if not result.get('success'):
            return create_error_response(
                message=f"Classification failed: {result.get('error', 'Unknown error')}"
            )
        
        return create_success_response(
            message="Case classified successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Classification failed: {str(e)}")
        return create_error_response(message=f"Classification failed: {str(e)}")


@router.post("/extract-entities", response_model=ApiResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    استخراج الكيانات القانونية من النص.
    
    **Legal Entity Extraction**:
    - Extracts parties (names)
    - Extracts dates
    - Extracts amounts/money
    - Extracts locations
    - Extracts document references
    - Extracts law mentions
    - Validates laws against knowledge base
    
    **Extracted Entities**:
    - **Parties**: أسماء الأطراف
    - **Dates**: التواريخ المهمة
    - **Amounts**: المبالغ المالية
    - **Locations**: الأماكن
    - **Documents**: المستندات المذكورة
    - **Laws**: القوانين المشار إليها
    
    **Request Body**:
    ```json
    {
      "case_text": "نص القضية هنا..."
    }
    ```
    
    **Example**:
    ```
    POST /api/v1/analysis/extract-entities
    ```
    """
    try:
        logger.info(f"📋 Extracting entities for user {current_user.sub}")
        
        # Initialize hybrid service
        hybrid_service = HybridAnalysisService(db)
        
        # Extract and validate entities
        result = await hybrid_service.extract_and_validate_entities(request.case_text)
        
        if not result.get('success'):
            return create_error_response(
                message=f"Entity extraction failed: {result.get('error', 'Unknown error')}"
            )
        
        entities = result.get('entities', {})
        total_entities = sum(len(v) for v in entities.values() if isinstance(v, list))
        
        return create_success_response(
            message=f"Extracted {total_entities} entities",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Entity extraction failed: {str(e)}")
        return create_error_response(message=f"Extraction failed: {str(e)}")


@router.post("/generate-strategy", response_model=ApiResponse)
async def generate_strategy(
    request: StrategyGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    توليد استراتيجية قانونية مفصلة.
    
    **Legal Strategy Generation**:
    - Based on previous analysis
    - Provides actionable steps
    - Documents needed
    - Witnesses to contact
    - Legal arguments
    - Negotiation strategy
    - Litigation strategy
    - Settlement options
    - Timeline and cost estimates
    - Success probability
    
    **Request Body**:
    ```json
    {
      "case_analysis": {
        ... تحليل القضية السابق ...
      }
    }
    ```
    
    **Example**:
    ```
    POST /api/v1/analysis/generate-strategy
    ```
    """
    try:
        logger.info(f"🎯 Generating strategy for user {current_user.sub}")
        
        # Initialize Gemini
        gemini = GeminiLegalAnalyzer()
        
        if not gemini.is_enabled():
            return create_error_response(message="Gemini AI is not enabled")
        
        # Generate strategy
        result = await gemini.generate_legal_strategy(request.case_analysis)
        
        if not result.get('success'):
            return create_error_response(
                message=f"Strategy generation failed: {result.get('error', 'Unknown error')}"
            )
        
        return create_success_response(
            message="Legal strategy generated successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Strategy generation failed: {str(e)}")
        return create_error_response(message=f"Strategy generation failed: {str(e)}")


@router.post("/answer-question", response_model=ApiResponse)
async def answer_legal_question(
    request: LegalQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    الإجابة على سؤال قانوني باستخدام RAG.
    
    **Legal Question Answering**:
    - Uses RAG for accurate answers
    - Retrieves relevant sources
    - Provides grounded responses
    - Includes source citations
    - Perfect for legal consultations
    
    **Context Types**:
    - `laws`: Search in laws only
    - `cases`: Search in cases only
    - `both`: Search in both (recommended)
    
    **Request Body**:
    ```json
    {
      "question": "ما هي حقوق العامل في حالة الفصل التعسفي؟",
      "context_type": "both"
    }
    ```
    
    **Response includes**:
    - Direct answer
    - Source laws
    - Source cases
    - Citations
    
    **Example**:
    ```
    POST /api/v1/analysis/answer-question
    ```
    """
    try:
        logger.info(f"❓ Answering question for user {current_user.sub}")
        logger.info(f"📝 Question: '{request.question}'")
        
        # Initialize RAG service
        rag_service = LegalRAGService(db)
        
        # Answer question
        result = await rag_service.answer_legal_question(
            question=request.question,
            context_type=request.context_type
        )
        
        if not result.get('success'):
            return create_error_response(
                message=f"Question answering failed: {result.get('error', 'Unknown error')}"
            )
        
        return create_success_response(
            message="Question answered successfully",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Question answering failed: {str(e)}")
        return create_error_response(message=f"Question answering failed: {str(e)}")
