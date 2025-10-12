"""
RAG Router - FastAPI endpoints for legal document processing and semantic search.

Provides REST API endpoints for:
- Document upload and processing (PDF/DOCX/TXT)
- Semantic search across law chunks
- System status and health checks
- Embedding service management
"""

import logging
import tempfile
import os
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, Body, File, UploadFile, Form
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


# Constants
ALLOWED_FILE_EXTENSIONS = {'.pdf', '.docx', '.txt'}
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MIN_QUERY_LENGTH = 2
MAX_TOP_K = 50
MIN_TOP_K = 1


def _validate_file_extension(filename: str) -> Optional[str]:
    """
    Validate file extension.
    
    Returns:
        File extension if valid, None otherwise
    """
    if '.' not in filename:
        return None
    
    extension = f".{filename.lower().split('.')[-1]}"
    return extension if extension in ALLOWED_FILE_EXTENSIONS else None


def _validate_file_size(file: UploadFile) -> tuple[bool, int]:
    """
    Validate file size.
    
    Returns:
        Tuple of (is_valid, file_size_bytes)
    """
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    return (file_size <= MAX_FILE_SIZE_BYTES, file_size)


async def _save_uploaded_file(file: UploadFile, extension: str) -> str:
    """
    Save uploaded file to temporary location.
    
    Returns:
        Path to temporary file
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
        content = await file.read()
        temp_file.write(content)
        return temp_file.name


def _cleanup_temp_file(file_path: str) -> None:
    """Safely remove temporary file."""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file: {e}")


def _validate_search_params(
    query: str,
    top_k: Optional[int],
    threshold: Optional[float]
) -> Optional[ApiResponse]:
    """
    Validate search parameters.
    
    Returns:
        Error response if validation fails, None if valid
    """
    if not query or len(query.strip()) < MIN_QUERY_LENGTH:
        return create_error_response(
            message="Invalid search query",
            errors=[ErrorDetail(
                field="query",
                message=f"Query must be at least {MIN_QUERY_LENGTH} characters"
            )]
        )
    
    if top_k and (top_k < MIN_TOP_K or top_k > MAX_TOP_K):
        return create_error_response(
            message="Invalid top_k parameter",
            errors=[ErrorDetail(
                field="top_k",
                message=f"top_k must be between {MIN_TOP_K} and {MAX_TOP_K}"
            )]
        )
    
    if threshold and (threshold < 0.0 or threshold > 1.0):
        return create_error_response(
            message="Invalid threshold parameter",
            errors=[ErrorDetail(
                field="threshold",
                message="threshold must be between 0.0 and 1.0"
            )]
        )
    
    return None


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
    Upload and process law document from file.
    
    Performs end-to-end processing:
    1. Validates file type and size
    2. Extracts text from document
    3. Generates smart chunks with context preservation
    4. Creates embeddings for semantic search
    5. Stores in database with metadata
    
    Supported formats: PDF, DOCX, TXT (max 50MB)
    """
    # Validate file extension
    file_extension = _validate_file_extension(file.filename)
    if not file_extension:
        return create_error_response(
            message="Unsupported file format",
            errors=[ErrorDetail(
                field="file",
                message=f"Supported: {', '.join([e.upper() for e in ALLOWED_FILE_EXTENSIONS])}"
            )]
        )
    
    # Validate file size
    is_valid_size, file_size = _validate_file_size(file)
    if not is_valid_size:
        return create_error_response(
            message="File too large",
            errors=[ErrorDetail(
                field="file",
                message=f"Max size: {MAX_FILE_SIZE_MB}MB (your file: {file_size/(1024*1024):.1f}MB)"
            )]
        )
    
    temp_path = None
    try:
        logger.info(f"Processing upload: {file.filename} for law: {law_name}")
        
        # Save uploaded file
        temp_path = await _save_uploaded_file(file, file_extension)
        
        # Prepare metadata
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
        
        # Cleanup
        _cleanup_temp_file(temp_path)
        
        # Format response
        if result['success']:
            return create_success_response(
                message=f"Document processed: {result['chunks_created']} chunks created",
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
                message=f"Processing failed: {result.get('error', 'Unknown error')}",
                errors=[ErrorDetail(message=result.get('error', 'Processing failed'))]
            )
        
    except Exception as e:
        if temp_path:
            _cleanup_temp_file(temp_path)
        
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
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
    Semantic search for relevant law chunks.
    
    Performs RAG-based search using:
    - Query embedding generation
    - Semantic similarity computation
    - Threshold filtering
    - Top-k ranking
    
    Returns matching chunks with similarity scores and metadata.
    """
    try:
        logger.info(f"Search: '{request.query[:50]}...' (k={request.top_k}, t={request.threshold})")
        
        # Validate parameters
        validation_error = _validate_search_params(
            request.query,
            request.top_k,
            request.threshold
        )
        if validation_error:
            return validation_error
        
        # Perform search
        rag_service = RAGService(db)
        search_result = await rag_service.search(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            law_source_id=request.law_source_id
        )
        
        if not search_result.get('success'):
            return create_error_response(
                message="Search failed",
                errors=[ErrorDetail(message=search_result.get('error', 'Search operation failed'))]
            )
        
        # Format response
        response_data = RAGSearchResponse(
            query=search_result['query'],
            total_results=search_result['total_results'],
            results=search_result['results'],
            processing_time=search_result['processing_time']
        )
        
        # Generate message
        count = search_result['total_results']
        if count == 0:
            message = "No relevant chunks found"
        elif count == 1:
            message = "Found 1 relevant chunk"
        else:
            message = f"Found {count} relevant chunks"
        
        logger.info(f"Search complete: {count} results in {search_result['processing_time']}s")
        
        return create_success_response(message=message, data=response_data)
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
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
    
    Returns:
    - System health status
    - Document and chunk counts
    - Embedding coverage metrics
    - Configuration settings
    - Model information
    """
    try:
        logger.info("Status check requested")
        
        rag_service = RAGService(db)
        system_status = await rag_service.get_system_status()
        
        if system_status.get('status') == 'error':
            return create_error_response(
                message="Failed to retrieve status",
                errors=[ErrorDetail(message=system_status.get('error', 'Unknown error'))]
            )
        
        # Get model info from embedding service
        try:
            embedding_stats = await rag_service.embedding_service.get_embedding_stats()
            model_info = embedding_stats.get('model', {})
        except Exception:
            model_info = {'model_name': 'unknown', 'model_dimension': 0}
        
        # Build enhanced status
        status_data = {
            'status': 'operational',
            'total_documents': system_status.get('total_documents', 0),
            'total_chunks': system_status.get('total_chunks', 0),
            'chunks_with_embeddings': system_status.get('chunks_with_embeddings', 0),
            'embedding_coverage': system_status.get('embedding_coverage', 0),
            'documents_by_status': system_status.get('documents_by_status', {}),
            'chunking_settings': system_status.get('chunking_settings', {}),
            'search_settings': {
                'default_top_k': 5,
                'default_threshold': 0.6,
                'max_top_k': MAX_TOP_K
            },
            'model_info': {
                'name': model_info.get('model_name', 'unknown'),
                'dimension': model_info.get('model_dimension', 0),
                'device': model_info.get('device', 'unknown')
            },
            'timestamp': system_status.get('timestamp')
        }
        
        logger.info(f"Status: {status_data['total_chunks']} chunks, {status_data['embedding_coverage']}% coverage")
        
        return create_success_response(
            message="RAG system operational",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return create_error_response(
            message=f"Failed to retrieve status: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )


@router.get("/embedding-status", response_model=ApiResponse[Dict[str, Any]])
async def get_embedding_status(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Get detailed embedding service status.
    
    Returns:
    - Model configuration
    - Cache performance metrics
    - Processing statistics
    - System health
    """
    try:
        logger.info("Embedding status check")
        
        rag_service = RAGService(db)
        embedding_stats = await rag_service.embedding_service.get_embedding_stats()
        
        return create_success_response(
            message="Embedding service healthy",
            data=embedding_stats
        )
        
    except Exception as e:
        logger.error(f"Embedding status check failed: {str(e)}")
        return create_error_response(
            message=f"Failed to retrieve embedding status: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )


@router.post("/validate-embeddings", response_model=ApiResponse[Dict[str, Any]])
async def validate_embeddings(
    sample_texts: List[str] = Body(None, description="Optional sample texts"),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Validate embedding quality with sample texts.
    
    Tests embedding service functionality and quality metrics.
    Useful for system health checks and debugging.
    """
    try:
        logger.info("Embedding validation requested")
        
        rag_service = RAGService(db)
        validation_result = await rag_service.embedding_service.validate_embedding_quality(
            sample_texts
        )
        
        if validation_result['success']:
            return create_success_response(
                message="Embedding validation successful",
                data=validation_result
            )
        else:
            return create_error_response(
                message="Embedding validation failed",
                errors=[ErrorDetail(message=validation_result.get('error', 'Validation failed'))],
                data=validation_result
            )
        
    except Exception as e:
        logger.error(f"Embedding validation failed: {str(e)}")
        return create_error_response(
            message=f"Validation failed: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )


@router.delete("/cache", response_model=ApiResponse[Dict[str, Any]])
async def clear_embedding_cache(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Clear embedding cache.
    
    Clears in-memory embedding cache and returns statistics.
    Useful for memory management and testing.
    """
    try:
        logger.info("Cache clearance requested")
        
        rag_service = RAGService(db)
        cache_stats = rag_service.embedding_service.clear_cache()
        
        return create_success_response(
            message="Cache cleared successfully",
            data=cache_stats
        )
        
    except Exception as e:
        logger.error(f"Cache clearance failed: {str(e)}")
        return create_error_response(
            message=f"Failed to clear cache: {str(e)}",
            errors=[ErrorDetail(message=str(e))]
        )
