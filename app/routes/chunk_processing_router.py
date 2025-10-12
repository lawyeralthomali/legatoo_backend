"""
Chunk Processing Router for API endpoints.

This module provides REST API endpoints for processing and managing
knowledge chunks with AI-powered text analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from ..services.legal.processing.chunk_processing_service import ChunkProcessingService
from ..db.database import get_db
from ..utils.auth import get_current_user
from ..models.user import User
from ..schemas.response import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chunks", tags=["Chunk Processing"])

@router.post("/documents/{document_id}/process", response_model=ApiResponse[Dict[str, Any]])
async def process_document_chunks(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process all chunks in a document and convert them to smart chunks.
    
    This endpoint uses AI-powered text analysis to split chunks into
    semantically meaningful legal text segments.
    
    Args:
        document_id: ID of the document to process
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Unified response with processing results
    """
    try:
        processing_service = ChunkProcessingService(db)
        result = await processing_service.process_document_chunks(document_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": result["message"],
                    "data": None,
                    "errors": result.get("errors", [])
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document chunks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Internal server error occurred while processing chunks",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )

@router.get("/documents/{document_id}/status", response_model=ApiResponse[Dict[str, Any]])
async def get_chunk_processing_status(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the chunk processing status for a specific document.
    
    Returns statistics about chunks including total count, embeddings count,
    and overall processing progress.
    
    Args:
        document_id: ID of the document
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Unified response with processing status
    """
    try:
        processing_service = ChunkProcessingService(db)
        status_data = await processing_service.get_processing_status(document_id)
        
        return {
            "success": True,
            "message": "Processing status retrieved successfully",
            "data": status_data,
            "errors": []
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve processing status",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )

@router.post("/documents/{document_id}/generate-embeddings", response_model=ApiResponse[Dict[str, Any]])
async def generate_chunk_embeddings(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate embeddings for all chunks in a specific document.
    
    Note: This endpoint is a placeholder for future implementation
    of vector embedding generation for semantic search capabilities.
    
    Args:
        document_id: ID of the document
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Unified response with embedding generation status
    """
    return {
        "success": True,
        "message": "Embedding generation endpoint - to be implemented",
        "data": {"document_id": document_id},
        "errors": []
    }