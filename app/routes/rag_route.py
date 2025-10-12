"""
Enhanced RAG Router - API endpoints for Document-Based Legal RAG System

This module provides REST API endpoints for RAG-based law document ingestion and search:
- /rag/upload-document: Ingest law documents directly from files
- /rag/search: Semantic search for relevant law chunks
- /rag/status: System status and statistics

All endpoints follow the unified API response format.
"""

import logging
import tempfile
import os
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Body, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.shared.rag_service import RAGService
from ..schemas.legal_knowledge import RAGSearchRequest, RAGSearchResponse
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


@router.post("/upload-document", response_model=ApiResponse[Dict])
async def upload_law_document(
    file: UploadFile = File(..., description="Law document file (PDF/DOCX/TXT)"),
    law_name: str = Form(..., description="Name of the law"),
    law_type: str = Form("law", description="Type of law"),
    jurisdiction: str = Form("السعودية", description="Jurisdiction"),
    description: str = Form(None, description="Optional description"),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict]:
    """
    Upload and process law document directly from file.
    
    This endpoint processes legal documents by:
    1. Validating file type and size
    2. Reading document content
    3. Smart text chunking with context preservation
    4. Generating embeddings for each chunk
    5. Storing chunks with document metadata
    
    **Supported Formats**: PDF, DOCX, TXT
    **Max File Size**: 50MB
    
    **Response Example**:
    ```json
    {
      "success": true,
      "message": "Law document processed successfully: 25 chunks created",
      "data": {
        "law_name": "نظام العمل السعودي",
        "chunks_created": 25,
        "chunks_stored": 25,
        "processing_time": 12.45,
        "file_type": "PDF",
        "total_words": 8450
      },
      "errors": []
    }
    ```
    
    **Error Response Example**:
    ```json
    {
      "success": false,
      "message": "Upload failed: Unsupported file format",
      "data": null,
      "errors": [
        {
          "field": "file",
          "message": "Only PDF, DOCX, and TXT files are supported"
        }
      ]
    }
    """
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    file_extension = f".{file.filename.lower().split('.')[-1]}" if '.' in file.filename else ''
    
    if file_extension not in allowed_extensions:
        return create_error_response(
            message="Unsupported file format",
            errors=[ErrorDetail(
                field="file",
                message=f"Supported formats: {', '.join([ext.upper() for ext in allowed_extensions])}"
            )]
        )
    
    # Validate file size (50MB max)
    max_size = 50 * 1024 * 1024  # 50MB
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        return create_error_response(
            message="File too large",
            errors=[ErrorDetail(
                field="file",
                message=f"Maximum file size is 50MB. Your file is {file_size / (1024*1024):.1f}MB"
            )]
        )
    
    # Create temporary file
    temp_file = None
    try:
        logger.info(f"📥 Document upload request: {file.filename} for law: {law_name}")
        
        # Create secure temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Prepare law metadata
        law_metadata = {
            'law_name': law_name,
            'law_type': law_type,
            'jurisdiction': jurisdiction,
            'description': description,
            'original_filename': file.filename,
            'file_size': file_size
        }
        
        # Process document
        rag_service = RAGService(db)
        result = await rag_service.ingest_law_document(temp_path, law_metadata)
        
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Failed to clean up temp file: {cleanup_error}")
        
        if result['success']:
            return create_success_response(
                message=f"✅ Law document processed successfully: {result['chunks_created']} chunks created",
                data={
                    'law_name': result['law_name'],
                    'chunks_created': result['chunks_created'],
                    'chunks_stored': result.get('chunks_stored', result['chunks_created']),
                    'processing_time': result['processing_time'],
                    'file_type': result.get('file_type', 'UNKNOWN'),
                    'total_words': result.get('total_words', 0)
                }
            )
        else:
            return create_error_response(
                message=f"❌ Failed to process document: {result.get('error', 'Unknown error')}",
                errors=[ErrorDetail(message=result.get('error', 'Processing failed'))]
            )
            
    except Exception as e:
        # Clean up temporary file in case of error
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except:
                pass
        
        logger.error(f"❌ Document upload failed: {str(e)}", exc_info=True)
        return create_error_response(
            message=f"Upload failed: {str(e)}",
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
    2. Computing semantic similarity with all law chunks
    3. Applying hybrid search (semantic + lexical)
    4. Filtering by similarity threshold
    5. Returning top-k most relevant chunks with metadata
    
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
            "word_count": 45,
            "metadata": {
              "law_name": "نظام العمل السعودي",
              "jurisdiction": "السعودية"
            }
          }
        ],
        "processing_time": 0.45
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"🔍 RAG Search: '{request.query[:50]}...' (top_k={request.top_k}, threshold={request.threshold})")
        
        # Validate parameters
        if not request.query or len(request.query.strip()) < 2:
            return create_error_response(
                message="Invalid search query",
                errors=[ErrorDetail(
                    field="query", 
                    message="Search query must be at least 2 characters long"
                )]
            )
        
        if request.top_k and (request.top_k < 1 or request.top_k > 50):
            return create_error_response(
                message="Invalid top_k parameter",
                errors=[ErrorDetail(
                    field="top_k",
                    message="top_k must be between 1 and 50"
                )]
            )
        
        if request.threshold and (request.threshold < 0.0 or request.threshold > 1.0):
            return create_error_response(
                message="Invalid threshold parameter",
                errors=[ErrorDetail(
                    field="threshold",
                    message="threshold must be between 0.0 and 1.0"
                )]
            )
        
        # Initialize RAG service and perform search
        rag_service = RAGService(db)
        search_result = await rag_service.search(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            law_source_id=request.law_source_id
        )
        
        if not search_result.get('success'):
            return create_error_response(
                message="Search operation failed",
                errors=[ErrorDetail(message=search_result.get('error', 'Search failed'))]
            )
        
        # Format response
        response_data = RAGSearchResponse(
            query=search_result['query'],
            total_results=search_result['total_results'],
            results=search_result['results'],
            processing_time=search_result['processing_time']
        )
        
        # Generate appropriate message
        if search_result['total_results'] == 0:
            message = "No relevant law chunks found"
        elif search_result['total_results'] == 1:
            message = "Found 1 relevant law chunk"
        else:
            message = f"Found {search_result['total_results']} relevant law chunks"
        
        logger.info(f"✅ Search completed: {search_result['total_results']} results in {search_result['processing_time']}s")
        
        return create_success_response(
            message=message,
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"❌ Search failed: {str(e)}", exc_info=True)
        return create_error_response(
            message=f"Search operation failed: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )


@router.get("/status", response_model=ApiResponse[Dict[str, Any]])
async def get_rag_status(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Get RAG system status and statistics.
    
    Returns comprehensive information about:
    - System health and operational status
    - Document and chunk statistics
    - Embedding coverage and model information
    - Performance metrics and settings
    
    **Response Example**:
    ```json
    {
      "success": true,
      "message": "RAG system is operational",
      "data": {
        "status": "operational",
        "total_chunks": 1532,
        "chunks_with_embeddings": 1532,
        "embedding_coverage": 100.0,
        "chunking_settings": {
          "max_chunk_words": 400,
          "min_chunk_words": 50,
          "chunk_overlap_words": 50
        },
        "search_settings": {
          "default_top_k": 5,
          "default_threshold": 0.6
        },
        "model_info": {
          "name": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
          "dimension": 768
        }
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info("📊 RAG status check requested")
        
        # Get system status from RAG service
        rag_service = RAGService(db)
        system_status = await rag_service.get_system_status()
        
        if system_status.get('status') == 'error':
            return create_error_response(
                message="Failed to retrieve system status",
                errors=[ErrorDetail(message=system_status.get('error', 'Unknown error'))]
            )
        
        # Enhanced status data
        status_data = {
            'status': 'operational',
            'total_chunks': system_status.get('total_chunks', 0),
            'chunks_with_embeddings': system_status.get('chunks_with_embeddings', 0),
            'embedding_coverage': system_status.get('embedding_coverage', 0),
            'chunking_settings': system_status.get('chunking_settings', {}),
            'search_settings': {
                'default_top_k': 5,
                'default_threshold': 0.6
            },
            'model_info': {
                'name': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
                'dimension': 768
            },
            'timestamp': system_status.get('timestamp')
        }
        
        logger.info(f"✅ RAG status: {status_data['total_chunks']} chunks, {status_data['embedding_coverage']}% coverage")
        
        return create_success_response(
            message="RAG system is operational",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get RAG status: {str(e)}")
        return create_error_response(
            message=f"Failed to retrieve system status: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )


@router.get("/embedding-status", response_model=ApiResponse[Dict[str, Any]])
async def get_embedding_status(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Get detailed embedding service status and statistics.
    
    Returns information about:
    - Embedding model configuration
    - Cache performance and statistics
    - Processing metrics
    - System health
    
    **Response Example**:
    ```json
    {
      "success": true,
      "message": "Embedding service is healthy",
      "data": {
        "status": "healthy",
        "cache": {
          "cache_size": 1245,
          "cache_hits": 8920,
          "cache_misses": 1560,
          "cache_hit_rate": 0.85
        },
        "model": {
          "model_name": "legal_optimized",
          "model_dimension": 768,
          "max_sequence_length": 512,
          "device": "cuda"
        },
        "performance": {
          "batch_size": 16,
          "max_text_length": 2000
        }
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info("🔧 Embedding status check requested")
        
        rag_service = RAGService(db)
        embedding_stats = await rag_service.embedding_service.get_embedding_stats()
        
        return create_success_response(
            message="Embedding service is healthy",
            data=embedding_stats
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get embedding status: {str(e)}")
        return create_error_response(
            message=f"Failed to retrieve embedding status: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )


@router.post("/validate-embeddings", response_model=ApiResponse[Dict[str, Any]])
async def validate_embeddings(
    sample_texts: List[str] = Body(None, description="Optional sample texts for validation"),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Validate embedding quality and performance.
    
    This endpoint tests the embedding service with sample texts
    to ensure proper functionality and quality.
    
    **Request Body Example**:
    ```json
    {
      "sample_texts": [
        "نص قانوني تجريبي للتحقق من جودة التضمين",
        "تحليل النصوص القانونية العربية",
        "بحث في التشريعات واللوائح"
      ]
    }
    ```
    """
    try:
        logger.info("🧪 Embedding validation requested")
        
        rag_service = RAGService(db)
        validation_result = await rag_service.embedding_service.validate_embedding_quality(sample_texts)
        
        if validation_result['success']:
            return create_success_response(
                message="Embedding validation completed successfully",
                data=validation_result
            )
        else:
            return create_error_response(
                message="Embedding validation failed",
                errors=[ErrorDetail(message=validation_result.get('error', 'Validation failed'))],
                data=validation_result
            )
        
    except Exception as e:
        logger.error(f"❌ Embedding validation failed: {str(e)}")
        return create_error_response(
            message=f"Embedding validation failed: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )


@router.delete("/cache", response_model=ApiResponse[Dict[str, Any]])
async def clear_embedding_cache(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Clear the embedding cache.
    
    This endpoint clears the in-memory embedding cache
    and returns cache statistics before clearing.
    
    **Response Example**:
    ```json
    {
      "success": true,
      "message": "Embedding cache cleared successfully",
      "data": {
        "cleared_entries": 1245,
        "previous_hits": 8920,
        "previous_misses": 1560
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info("🧹 Embedding cache clearance requested")
        
        rag_service = RAGService(db)
        cache_stats = rag_service.embedding_service.clear_cache()
        
        return create_success_response(
            message="Embedding cache cleared successfully",
            data=cache_stats
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {str(e)}")
        return create_error_response(
            message=f"Failed to clear cache: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )