"""
Embedding Router - API endpoints for embedding generation and similarity search

Provides endpoints for:
- Generating embeddings for documents and chunks
- Searching for similar chunks
- Checking embedding status
- Model information
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal.search.arabic_legal_embedding_service import ArabicLegalEmbeddingService
from ..utils.auth import get_current_user
from ..models.user import User
from ..schemas.embedding import (
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    DocumentEmbeddingStatus,
    GlobalEmbeddingStatus,
    DocumentProcessingResponse,
    BatchProcessingResponse,
    ChunkSimilarity,
    EmbeddingModelInfo
)
from ..schemas.response import ApiResponse, create_success_response, create_error_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/embeddings",
    tags=["Embeddings"]
)


@router.post("/documents/{document_id}/generate", response_model=ApiResponse)
async def generate_document_embeddings(
    document_id: int,
    overwrite: bool = Query(False, description="Overwrite existing embeddings"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    يولد embeddings لكل الـ chunks في document محدد.
    
    **Process**:
    1. Fetch all chunks for the document
    2. Generate embeddings using multilingual model
    3. Store embeddings in database
    4. Return processing statistics
    
    **Parameters**:
    - document_id: ID of the document to process
    - overwrite: If true, regenerate embeddings for chunks that already have them
    
    **Returns**:
    - Success response with processing statistics
    
    **Example Response**:
    ```json
    {
      "success": true,
      "message": "Generated embeddings for 45 chunks in document 123",
      "data": {
        "document_id": 123,
        "total_chunks": 45,
        "processed_chunks": 45,
        "failed_chunks": 0,
        "processing_time": "15.2s"
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"📄 Generate embeddings request for document {document_id} by user {current_user.id}")
        
        # Initialize Arabic legal embedding service
        embedding_service = ArabicLegalEmbeddingService(db, use_faiss=True)
        embedding_service.initialize_model()
        
        # Generate embeddings
        result = await embedding_service.generate_document_embeddings(
            document_id=document_id,
            overwrite=overwrite
        )
        
        if not result.get("success", False):
            return create_error_response(
                message=f"Failed to generate embeddings: {result.get('error', 'Unknown error')}"
            )
        
        # Format response
        message = f"Generated embeddings for {result['processed_chunks']} chunks in document {document_id}"
        if result['failed_chunks'] > 0:
            message += f" ({result['failed_chunks']} failed)"
        
        return create_success_response(
            message=message,
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to generate document embeddings: {str(e)}")
        return create_error_response(
            message=f"Failed to generate embeddings: {str(e)}"
        )


@router.post("/chunks/batch-generate", response_model=ApiResponse)
async def generate_batch_embeddings(
    chunk_ids: List[int] = Query(..., description="List of chunk IDs (max 1000)"),
    overwrite: bool = Query(False, description="Overwrite existing embeddings"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    يولد embeddings لمجموعة من الـ chunks.
    
    **Process**:
    1. Validate chunk IDs (max 1000)
    2. Generate embeddings in batches
    3. Store in database
    4. Return statistics
    
    **Parameters**:
    - chunk_ids: List of chunk IDs to process (max 1000)
    - overwrite: Regenerate existing embeddings
    
    **Returns**:
    - Success response with processing statistics
    
    **Example Request**:
    ```
    POST /api/v1/embeddings/chunks/batch-generate?chunk_ids=1&chunk_ids=2&chunk_ids=3
    ```
    
    **Example Response**:
    ```json
    {
      "success": true,
      "message": "Generated embeddings for 3 chunks",
      "data": {
        "total_chunks": 3,
        "processed_chunks": 3,
        "failed_chunks": 0,
        "processing_time": "2.5s"
      },
      "errors": []
    }
    ```
    """
    try:
        # Validate chunk IDs count
        if len(chunk_ids) == 0:
            return create_error_response(
                message="No chunk IDs provided"
            )
        
        if len(chunk_ids) > 1000:
            return create_error_response(
                message="Cannot process more than 1000 chunks at once"
            )
        
        logger.info(f"📦 Batch generate request for {len(chunk_ids)} chunks by user {current_user.id}")
        
        # Initialize Arabic legal embedding service
        embedding_service = ArabicLegalEmbeddingService(db, use_faiss=True)
        embedding_service.initialize_model()
        
        # Generate embeddings
        result = await embedding_service.generate_batch_embeddings(
            chunk_ids=chunk_ids,
            overwrite=overwrite
        )
        
        if not result.get("success", False):
            return create_error_response(
                message=f"Failed to generate embeddings: {result.get('error', 'Unknown error')}"
            )
        
        # Format response
        message = f"Generated embeddings for {result['processed_chunks']} chunks"
        if result['failed_chunks'] > 0:
            message += f" ({result['failed_chunks']} failed)"
        
        return create_success_response(
            message=message,
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to generate batch embeddings: {str(e)}")
        return create_error_response(
            message=f"Failed to generate embeddings: {str(e)}"
        )


@router.post("/search/similar", response_model=ApiResponse)
async def search_similar_chunks(
    query: str = Query(..., description="Search query text", min_length=3),
    top_k: int = Query(10, description="Number of results", ge=1, le=100),
    threshold: float = Query(0.7, description="Similarity threshold", ge=0.0, le=1.0),
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    case_id: Optional[int] = Query(None, description="Filter by case ID"),
    law_source_id: Optional[int] = Query(None, description="Filter by law source ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    يبحث عن الـ chunks الأكثر تشابهاً مع query باستخدام semantic search.
    
    **Process**:
    1. Generate embedding for search query
    2. Calculate cosine similarity with all stored embeddings
    3. Filter by threshold
    4. Return top K results sorted by similarity
    
    **Parameters**:
    - query: Search query text (Arabic or English)
    - top_k: Number of top results to return (1-100)
    - threshold: Minimum similarity score (0.0-1.0)
    - document_id: Optional filter by document
    - case_id: Optional filter by case
    - law_source_id: Optional filter by law source
    
    **Returns**:
    - List of similar chunks with similarity scores
    
    **Example Request**:
    ```
    POST /api/v1/embeddings/search/similar?query=فسخ العقد بدون إنذار&top_k=5&threshold=0.7
    ```
    
    **Example Response**:
    ```json
    {
      "success": true,
      "message": "Found 5 similar chunks",
      "data": {
        "query": "فسخ العقد بدون إنذار",
        "results": [
          {
            "chunk_id": 456,
            "content": "يجوز لصاحب العمل فسخ العقد دون إنذار...",
            "similarity": 0.89,
            "document_id": 123,
            "chunk_index": 10,
            "article_id": 75
          }
        ],
        "total_results": 5,
        "threshold": 0.7
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"🔍 Similar search request: '{query[:50]}...' by user {current_user.id}")
        
        # Validate query
        if not query or len(query.strip()) < 3:
            return create_error_response(
                message="Query must be at least 3 characters"
            )
        
        # Initialize Arabic legal embedding service
        embedding_service = ArabicLegalEmbeddingService(db, use_faiss=True)
        embedding_service.initialize_model()
        
        # Build filters
        filters = {}
        if document_id:
            filters['document_id'] = document_id
        if case_id:
            filters['case_id'] = case_id
        if law_source_id:
            filters['law_source_id'] = law_source_id
        
        # Search for similar chunks
        results = await embedding_service.find_similar_chunks(
            query=query.strip(),
            top_k=top_k,
            threshold=threshold,
            filters=filters if filters else None
        )
        
        # Format response
        response_data = {
            "query": query.strip(),
            "results": results,
            "total_results": len(results),
            "threshold": threshold
        }
        
        message = f"Found {len(results)} similar chunks"
        if filters:
            message += f" (with filters)"
        
        return create_success_response(
            message=message,
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to search similar chunks: {str(e)}")
        return create_error_response(
            message=f"Failed to search: {str(e)}"
        )


@router.get("/documents/{document_id}/status", response_model=ApiResponse)
async def get_document_embedding_status(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    يعرض حالة الـ embeddings لـ document محدد.
    
    **Returns**:
    - Total chunks
    - Chunks with embeddings
    - Chunks without embeddings
    - Completion percentage
    - Status (complete, partial, not_started)
    
    **Example Response**:
    ```json
    {
      "success": true,
      "message": "Embedding status for document 123",
      "data": {
        "document_id": 123,
        "total_chunks": 45,
        "chunks_with_embeddings": 45,
        "chunks_without_embeddings": 0,
        "completion_percentage": 100.0,
        "status": "complete"
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"📊 Embedding status request for document {document_id}")
        
        # Initialize Arabic legal embedding service
        embedding_service = ArabicLegalEmbeddingService(db, use_faiss=True)
        embedding_service.initialize_model()
        
        # Get status
        result = await embedding_service.get_embedding_status(document_id)
        
        if not result.get("success", False):
            return create_error_response(
                message=f"Failed to get embedding status: {result.get('error', 'Unknown error')}"
            )
        
        return create_success_response(
            message=f"Embedding status for document {document_id}",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get embedding status: {str(e)}")
        return create_error_response(
            message=f"Failed to get status: {str(e)}"
        )


@router.get("/status", response_model=ApiResponse)
async def get_global_embedding_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    يعرض حالة الـ embeddings لكل النظام.
    
    **Returns**:
    - Total chunks in system
    - Chunks with embeddings
    - Chunks without embeddings
    - Completion percentage
    - Model information
    
    **Example Response**:
    ```json
    {
      "success": true,
      "message": "Global embedding status",
      "data": {
        "total_chunks": 1250,
        "chunks_with_embeddings": 1000,
        "chunks_without_embeddings": 250,
        "completion_percentage": 80.0,
        "model_name": "default",
        "device": "cuda"
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"📊 Global embedding status request by user {current_user.id}")
        
        # Initialize Arabic legal embedding service
        embedding_service = ArabicLegalEmbeddingService(db, use_faiss=True)
        embedding_service.initialize_model()
        
        # Get status
        result = await embedding_service.get_global_embedding_status()
        
        if not result.get("success", False):
            return create_error_response(
                message=f"Failed to get global status: {result.get('error', 'Unknown error')}"
            )
        
        return create_success_response(
            message="Global embedding status",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get global status: {str(e)}")
        return create_error_response(
            message=f"Failed to get status: {str(e)}"
        )


@router.get("/model-info", response_model=ApiResponse)
async def get_model_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    يعرض معلومات عن نموذج الـ embeddings المستخدم.
    
    **Returns**:
    - Model name
    - Model path
    - Embedding dimension
    - Device (CPU/GPU)
    - Configuration
    
    **Example Response**:
    ```json
    {
      "success": true,
      "message": "Embedding model information",
      "data": {
        "model_name": "default",
        "model_path": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "embedding_dimension": 768,
        "device": "cuda",
        "max_seq_length": 512,
        "batch_size": 32
      },
      "errors": []
    }
    ```
    """
    try:
        logger.info(f"ℹ️ Model info request by user {current_user.id}")
        
        # Initialize Arabic legal embedding service
        embedding_service = ArabicLegalEmbeddingService(db, use_faiss=True)
        embedding_service.initialize_model()
        
        # Get model info
        model_info = {
            "model_name": embedding_service.model_name,
            "model_path": embedding_service.MODELS.get(
                embedding_service.model_name,
                embedding_service.MODELS['default']
            ),
            "embedding_dimension": embedding_service.model.get_sentence_embedding_dimension(),
            "device": embedding_service.device,
            "max_seq_length": embedding_service.max_seq_length,
            "batch_size": embedding_service.batch_size
        }
        
        return create_success_response(
            message="Embedding model information",
            data=model_info
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get model info: {str(e)}")
        return create_error_response(
            message=f"Failed to get model info: {str(e)}"
        )
