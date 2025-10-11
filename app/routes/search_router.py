"""
Search Router - API endpoints for semantic search

Provides REST API endpoints for semantic search across legal documents.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.arabic_legal_search_service import ArabicLegalSearchService
from ..utils.auth import get_current_user
from ..schemas.profile_schemas import TokenData
from ..schemas.search import (
    SimilarSearchRequest,
    SimilarCasesRequest,
    HybridSearchRequest,
    SearchSuggestionsRequest,
    SearchResultsResponse,
    HybridSearchResponse,
    SearchSuggestionsResponse,
    SearchStatisticsResponse
)
from ..schemas.response import ApiResponse, create_success_response, create_error_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/search",
    tags=["Semantic Search"]
)


@router.post("/similar-laws", response_model=ApiResponse)
async def search_similar_laws(
    request: SimilarSearchRequest = Body(..., description="Search request parameters"),
    db: AsyncSession = Depends(get_db),
    #current_user: TokenData = Depends(get_current_user)
):
    
    try:
        #logger.info(f"🔍 Similar laws search: '{request.query[:50]}...' by user {current_user.sub}")
        
        # Build filters from request
        filters = {}
        if request.jurisdiction:
            filters['jurisdiction'] = request.jurisdiction
        if request.law_source_id:
            filters['law_source_id'] = request.law_source_id
        
        # Initialize Arabic legal search service
        search_service = ArabicLegalSearchService(db, use_faiss=True)
        
        # 🔥 CRITICAL FIX: Initialize the service (load model + build FAISS index)
        await search_service.initialize()
        
        # Perform search (using STANDARD search for testing, not FAISS)
        results = await search_service.find_similar_laws(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            filters=filters if filters else None,
            use_fast_search=False  # 🧪 Testing standard search (non-FAISS)
        )
        
        # Format response
        response_data = {
            "query": request.query,
            "results": results,
            "total_results": len(results),
            "threshold": request.threshold
        }
        
        message = f"Found {len(results)} similar laws"
        if filters:
            message += " (with filters)"
        
        return create_success_response(
            message=message,
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to search similar laws: {str(e)}")
        return create_error_response(
            message=f"Failed to search: {str(e)}"
        )


@router.post("/similar-cases", response_model=ApiResponse)
async def search_similar_cases(
    request: SimilarCasesRequest = Body(..., description="Search request parameters"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    يبحث عن القضايا القانونية المشابهة للاستعلام.
    
    **Semantic Search for Legal Cases**:
    - Find similar historical cases and precedents
    - AI-powered semantic matching
    - Filter by case type, court level, jurisdiction
    
    **Parameters**:
    - query: Your search query
    - top_k: Number of results (1-100)
    - threshold: Similarity threshold (0.0-1.0)
    - jurisdiction: Filter by jurisdiction (optional)
    - case_type: Filter by type (مدني, جنائي, تجاري, عمل, إداري)
    - court_level: Filter by level (ابتدائي, استئناف, تمييز, عالي)
    
    **Example Request Body**:
    ```json
    {
      "query": "إنهاء خدمات عامل",
      "top_k": 10,
      "threshold": 0.7,
      "case_type": "عمل",
      "court_level": "ابتدائي",
      "jurisdiction": "المملكة العربية السعودية"
    }
    ```
    
    **Response**:
    ```json
    {
      "success": true,
      "message": "Found 5 similar cases",
      "data": {
        "query": "إنهاء خدمات عامل",
        "results": [
          {
            "chunk_id": 456,
            "content": "قضية إنهاء خدمات عامل بدون مبرر...",
            "similarity": 0.85,
            "source_type": "case",
            "case_metadata": {
              "case_number": "123/2024",
              "title": "قضية عمالية",
              "case_type": "عمل"
            }
          }
        ],
        "total_results": 5
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"🔍 Similar cases search: '{request.query[:50]}...' by user {current_user.sub}")
        
        # Build filters from request
        filters = {}
        if request.jurisdiction:
            filters['jurisdiction'] = request.jurisdiction
        if request.case_type:
            filters['case_type'] = request.case_type
        if request.court_level:
            filters['court_level'] = request.court_level
        if request.case_id:
            filters['case_id'] = request.case_id
        
        # Initialize Arabic legal search service
        search_service = ArabicLegalSearchService(db, use_faiss=True)
        
        # 🔥 CRITICAL FIX: Initialize the service (load model + build FAISS index)
        await search_service.initialize()
        
        # Perform search
        results = await search_service.find_similar_cases(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            filters=filters if filters else None
        )
        
        # Format response
        response_data = {
            "query": request.query,
            "results": results,
            "total_results": len(results),
            "threshold": request.threshold
        }
        
        message = f"Found {len(results)} similar cases"
        if filters:
            message += " (with filters)"
        
        return create_success_response(
            message=message,
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to search similar cases: {str(e)}")
        return create_error_response(
            message=f"Failed to search: {str(e)}"
        )


@router.post("/hybrid", response_model=ApiResponse)
async def hybrid_search(
    request: HybridSearchRequest = Body(..., description="Hybrid search request parameters"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    بحث هجين عبر أنواع مختلفة من المستندات القانونية.
    
    **Hybrid Search Across Multiple Document Types**:
    - Search laws and cases simultaneously
    - Get comprehensive results in one request
    - Compare relevance across different sources
    
    **Parameters**:
    - query: Your search query
    - search_types: Types to search (laws, cases, or all)
    - top_k: Results per type (1-50)
    - threshold: Similarity threshold (0.0-1.0)
    - jurisdiction: Filter by jurisdiction (optional)
    
    **Example Request Body**:
    ```json
    {
      "query": "حقوق العامل",
      "search_types": ["laws", "cases"],
      "top_k": 5,
      "threshold": 0.6,
      "jurisdiction": "المملكة العربية السعودية"
    }
    ```
    
    **Response**:
    ```json
    {
      "success": true,
      "message": "Found 10 total results across 2 types",
      "data": {
        "query": "حقوق العامل",
        "search_types": ["laws", "cases"],
        "total_results": 10,
        "laws": {
          "count": 5,
          "results": [...]
        },
        "cases": {
          "count": 5,
          "results": [...]
        }
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"🔍 Hybrid search: '{request.query[:50]}...' by user {current_user.sub}")
        
        # Build filters from request
        filters = {}
        if request.jurisdiction:
            filters['jurisdiction'] = request.jurisdiction
        
        # Initialize Arabic legal search service
        search_service = ArabicLegalSearchService(db, use_faiss=True)
        
        # 🔥 CRITICAL FIX: Initialize the service (load model + build FAISS index)
        await search_service.initialize()
        
        # Perform hybrid search
        results = await search_service.hybrid_search(
            query=request.query,
            search_types=request.search_types,
            top_k=request.top_k,
            threshold=request.threshold,
            filters=filters if filters else None
        )
        
        total = results.get('total_results', 0)
        message = f"Found {total} total results"
        if len(request.search_types) > 1:
            message += f" across {len(request.search_types)} types"
        
        return create_success_response(
            message=message,
            data=results
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to perform hybrid search: {str(e)}")
        return create_error_response(
            message=f"Failed to search: {str(e)}"
        )


@router.get("/suggestions", response_model=ApiResponse)
async def get_search_suggestions(
    partial_query: str = Query(..., description="Partial search query", min_length=1),
    limit: int = Query(5, description="Maximum suggestions", ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    الحصول على اقتراحات بحث بناءً على استعلام جزئي.
    
    **Search Suggestions / Auto-complete**:
    - Get search suggestions as user types
    - Based on law names and case titles
    - Helps users find relevant content faster
    
    **Parameters**:
    - partial_query: Partial search text
    - limit: Maximum number of suggestions (1-20)
    
    **Example**:
    ```
    GET /api/v1/search/suggestions?partial_query=نظام+ال&limit=5
    ```
    
    **Response**:
    ```json
    {
      "success": true,
      "message": "Found 5 suggestions",
      "data": {
        "partial_query": "نظام ال",
        "suggestions": [
          "نظام العمل",
          "نظام المحاكم التجارية",
          "نظام المرافعات الشرعية"
        ],
        "count": 3
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"💡 Search suggestions for: '{partial_query}' by user {current_user.sub}")
        
        # Initialize Arabic legal search service
        search_service = ArabicLegalSearchService(db, use_faiss=True)
        
        # Note: Suggestions don't need full initialization
        
        # Get suggestions
        suggestions = await search_service.get_search_suggestions(
            partial_query=partial_query,
            limit=limit
        )
        
        response_data = {
            "partial_query": partial_query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
        return create_success_response(
            message=f"Found {len(suggestions)} suggestions",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get suggestions: {str(e)}")
        return create_error_response(
            message=f"Failed to get suggestions: {str(e)}"
        )


@router.get("/statistics", response_model=ApiResponse)
async def get_search_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    الحصول على إحصائيات البحث والمحتوى القابل للبحث.
    
    **Search Statistics**:
    - Total searchable chunks
    - Law chunks count
    - Case chunks count
    - Cache statistics
    
    **Example**:
    ```
    GET /api/v1/search/statistics
    ```
    
    **Response**:
    ```json
    {
      "success": true,
      "message": "Search statistics",
      "data": {
        "total_searchable_chunks": 818,
        "law_chunks": 600,
        "case_chunks": 218,
        "cache_size": 15,
        "cache_enabled": true
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"📊 Getting search statistics for user {current_user.sub}")
        
        # Initialize Arabic legal search service
        search_service = ArabicLegalSearchService(db, use_faiss=True)
        
        # Get statistics
        stats = await search_service.get_statistics()
        
        return create_success_response(
            message="Search statistics",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get statistics: {str(e)}")
        return create_error_response(
            message=f"Failed to get statistics: {str(e)}"
        )


@router.post("/clear-cache", response_model=ApiResponse)
async def clear_search_cache(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    مسح ذاكرة التخزين المؤقت للبحث.
    
    **Clear Search Cache**:
    - Clears the in-memory query cache
    - Useful after updating embeddings
    - Admin/maintenance operation
    
    **Example**:
    ```
    POST /api/v1/search/clear-cache
    ```
    
    **Response**:
    ```json
    {
      "success": true,
      "message": "Search cache cleared successfully",
      "data": {
        "cache_cleared": true
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"🗑️ Clearing search cache by user {current_user.sub}")
        
        # Initialize Arabic legal search service
        search_service = ArabicLegalSearchService(db, use_faiss=True)
        
        # Clear cache
        search_service.clear_cache()
        
        return create_success_response(
            message="Search cache cleared successfully",
            data={"cache_cleared": True}
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {str(e)}")
        return create_error_response(
            message=f"Failed to clear cache: {str(e)}"
        )
