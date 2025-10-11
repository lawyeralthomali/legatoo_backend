"""
RAG Router - API endpoints for Retrieval-Augmented Generation on Legal Laws

This module provides REST API endpoints for RAG-based law ingestion and search:
- /rag/upload: Ingest law data from JSON
- /rag/search: Semantic search for relevant law chunks

All endpoints follow the unified API response format defined in .cursorrules.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, Body, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.rag_service import RAGService
from ..schemas.legal_knowledge import (
    RAGLawUploadRequest,
    RAGSearchRequest,
    RAGUploadResponse,
    RAGSearchResponse
)
from ..schemas.response import (
    ApiResponse,
    create_success_response,
    create_error_response,
    ErrorDetail
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/rag",
    tags=["RAG - Legal Laws"]
)


@router.post("/upload", response_model=ApiResponse[RAGUploadResponse])
async def upload_law_json(
    request: RAGLawUploadRequest = Body(..., description="Law data in JSON format"),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[RAGUploadResponse]:
    """
    Upload and ingest law data from JSON.
    
    This endpoint processes legal law documents by:
    1. Validating the JSON structure
    2. Creating LawSource and LawArticle entries
    3. Splitting content into semantic chunks
    4. Generating embeddings for each chunk
    5. Storing chunks with proper hierarchical linkage
    
    **Request Body Example**:
    ```json
    {
      "law_name": "نظام العمل السعودي",
      "law_type": "law",
      "jurisdiction": "المملكة العربية السعودية",
      "issuing_authority": "وزارة الموارد البشرية والتنمية الاجتماعية",
      "issue_date": "2005-09-27",
      "description": "نظام ينظم علاقات العمل في المملكة",
      "source_url": "https://example.com/labor-law",
      "articles": [
        {
          "article_number": "1",
          "title": "التعريفات",
          "content": "يقصد بالألفاظ والعبارات الآتية المعاني المبينة أمامها...",
          "keywords": ["تعريفات", "مصطلحات"]
        },
        {
          "article_number": "2",
          "title": "نطاق التطبيق",
          "content": "يطبق هذا النظام على...",
          "keywords": ["نطاق", "تطبيق"]
        }
      ]
    }
    ```
    
    **Response Example**:
    ```json
    {
      "success": true,
      "message": "Law uploaded and processed successfully",
      "data": {
        "law_source_id": 123,
        "law_name": "نظام العمل السعودي",
        "articles_created": 2,
        "chunks_created": 15,
        "processing_time": 3.45,
        "status": "processed"
      },
      "errors": []
    }
    ```
    
    **Error Response Example**:
    ```json
    {
      "success": false,
      "message": "Failed to upload law: Invalid JSON structure",
      "data": null,
      "errors": [
        {
          "field": "articles",
          "message": "Articles list cannot be empty"
        }
      ]
    }
    ```
    """
    try:
        logger.info(f"📥 RAG Upload request for law: {request.law_name}")
        
        # Initialize RAG service
        rag_service = RAGService(db)
        
        # Convert Pydantic model to dict for processing
        json_data = {
            'law_name': request.law_name,
            'law_type': request.law_type.value,
            'jurisdiction': request.jurisdiction,
            'issuing_authority': request.issuing_authority,
            'issue_date': request.issue_date,
            'last_update': request.last_update,
            'description': request.description,
            'source_url': request.source_url,
            'articles': [
                {
                    'article_number': article.article_number,
                    'title': article.title,
                    'content': article.content,
                    'keywords': article.keywords
                }
                for article in request.articles
            ]
        }
        
        # Process law ingestion
        result = await rag_service.ingest_law_json(json_data)
        
        if not result.get('success'):
            return create_error_response(
                message="Law upload failed",
                errors=[ErrorDetail(message="Failed to process law data")]
            )
        
        # Format response
        response_data = RAGUploadResponse(
            law_source_id=result['law_source_id'],
            law_name=result['law_name'],
            articles_created=result['articles_created'],
            chunks_created=result['chunks_created'],
            processing_time=result['processing_time'],
            status=result['status']
        )
        
        logger.info(f"✅ Law uploaded successfully: {result['law_source_id']}")
        
        return create_success_response(
            message="Law uploaded and processed successfully",
            data=response_data
        )
        
    except ValueError as e:
        # Validation errors
        logger.error(f"❌ Validation error: {str(e)}")
        return create_error_response(
            message=f"Validation failed: {str(e)}",
            errors=[ErrorDetail(field="validation", message=str(e))]
        )
        
    except Exception as e:
        # General errors
        logger.error(f"❌ Law upload failed: {str(e)}", exc_info=True)
        return create_error_response(
            message=f"Failed to upload law: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )


@router.post("/search", response_model=ApiResponse[RAGSearchResponse])
async def search_law_chunks(
    request: RAGSearchRequest = Body(..., description="Search query parameters"),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[RAGSearchResponse]:
    """
    Search for relevant law chunks using semantic similarity.
    
    This endpoint performs RAG-based search by:
    1. Generating embedding for the query
    2. Computing cosine similarity with all law chunks
    3. Filtering by similarity threshold
    4. Returning top-k most relevant chunks with metadata
    
    **Request Body Example**:
    ```json
    {
      "query": "ما هي حقوق العامل عند إنهاء عقد العمل؟",
      "top_k": 5,
      "threshold": 0.6,
      "law_source_id": null
    }
    ```
    
    **Parameters**:
    - `query` (required): Search query or question in Arabic/English
    - `top_k` (optional): Number of results to return (1-50, default: 5)
    - `threshold` (optional): Minimum similarity score (0.0-1.0, default: 0.6)
    - `law_source_id` (optional): Filter by specific law source ID
    
    **Response Example**:
    ```json
    {
      "success": true,
      "message": "Found 5 relevant law chunks",
      "data": {
        "query": "ما هي حقوق العامل عند إنهاء عقد العمل؟",
        "total_results": 5,
        "results": [
          {
            "chunk_id": 123,
            "content": "للعامل الحق في مكافأة نهاية الخدمة عند إنهاء عقد العمل...",
            "similarity_score": 0.8745,
            "law_source_id": 1,
            "law_source_name": "نظام العمل السعودي",
            "article_id": 45,
            "article_number": "84",
            "article_title": "مكافأة نهاية الخدمة"
          },
          {
            "chunk_id": 124,
            "content": "لا يجوز لصاحب العمل إنهاء العقد دون مكافأة أو تعويض...",
            "similarity_score": 0.8234,
            "law_source_id": 1,
            "law_source_name": "نظام العمل السعودي",
            "article_id": 46,
            "article_number": "77",
            "article_title": "إنهاء عقد العمل"
          }
        ],
        "processing_time": 0.45
      },
      "errors": []
    }
    ```
    
    **No Results Example**:
    ```json
    {
      "success": true,
      "message": "No relevant law chunks found",
      "data": {
        "query": "irrelevant query",
        "total_results": 0,
        "results": [],
        "processing_time": 0.23
      },
      "errors": []
    }
    ```
    
    **Use Cases**:
    - Legal research and document retrieval
    - Question answering systems
    - Legal chatbot context retrieval
    - Similar law article discovery
    - Compliance checking
    """
    try:
        logger.info(f"🔍 RAG Search: '{request.query[:50]}...' (top_k={request.top_k})")
        
        # Initialize RAG service
        rag_service = RAGService(db)
        
        # Perform search
        search_result = await rag_service.search(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            law_source_id=request.law_source_id
        )
        
        if not search_result.get('success'):
            return create_error_response(
                message="Search failed",
                errors=[ErrorDetail(message="Failed to perform search")]
            )
        
        # Format response
        response_data = RAGSearchResponse(
            query=search_result['query'],
            total_results=search_result['total_results'],
            results=search_result['results'],
            processing_time=search_result['processing_time']
        )
        
        # Determine message
        if search_result['total_results'] == 0:
            message = "No relevant law chunks found"
        elif search_result['total_results'] == 1:
            message = "Found 1 relevant law chunk"
        else:
            message = f"Found {search_result['total_results']} relevant law chunks"
        
        logger.info(f"✅ Search completed: {search_result['total_results']} results")
        
        return create_success_response(
            message=message,
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"❌ Search failed: {str(e)}", exc_info=True)
        return create_error_response(
            message=f"Failed to search: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )


@router.get("/status", response_model=ApiResponse[Dict[str, Any]])
async def get_rag_status(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Get RAG system status and statistics.
    
    Returns information about:
    - Total law sources
    - Total articles
    - Total chunks with embeddings
    - Embedding model information
    
    **Response Example**:
    ```json
    {
      "success": true,
      "message": "RAG system is operational",
      "data": {
        "status": "operational",
        "total_law_sources": 5,
        "total_articles": 245,
        "total_chunks": 1532,
        "chunks_with_embeddings": 1532,
        "embedding_coverage": 100.0,
        "model": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info("📊 RAG status check requested")
        
        from sqlalchemy import select, func
        from ..models.legal_knowledge import LawSource, LawArticle, KnowledgeChunk
        
        # Get counts
        law_sources_result = await db.execute(select(func.count(LawSource.id)))
        total_law_sources = law_sources_result.scalar() or 0
        
        articles_result = await db.execute(select(func.count(LawArticle.id)))
        total_articles = articles_result.scalar() or 0
        
        chunks_result = await db.execute(
            select(func.count(KnowledgeChunk.id)).where(
                KnowledgeChunk.law_source_id.isnot(None)
            )
        )
        total_chunks = chunks_result.scalar() or 0
        
        chunks_with_embeddings_result = await db.execute(
            select(func.count(KnowledgeChunk.id)).where(
                KnowledgeChunk.law_source_id.isnot(None),
                KnowledgeChunk.embedding_vector.isnot(None),
                KnowledgeChunk.embedding_vector != ''
            )
        )
        chunks_with_embeddings = chunks_with_embeddings_result.scalar() or 0
        
        # Calculate coverage
        coverage = (chunks_with_embeddings / total_chunks * 100) if total_chunks > 0 else 0.0
        
        status_data = {
            'status': 'operational',
            'total_law_sources': total_law_sources,
            'total_articles': total_articles,
            'total_chunks': total_chunks,
            'chunks_with_embeddings': chunks_with_embeddings,
            'embedding_coverage': round(coverage, 2),
            'model': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
        }
        
        logger.info(f"✅ RAG status: {total_law_sources} sources, {total_articles} articles, {total_chunks} chunks")
        
        return create_success_response(
            message="RAG system is operational",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get RAG status: {str(e)}")
        return create_error_response(
            message=f"Failed to retrieve status: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )

