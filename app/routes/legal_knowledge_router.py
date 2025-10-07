"""
Legal Knowledge Processing API Router

This router provides API endpoints for extracting metadata and articles
from legal documents using AI-powered analysis.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal_knowledge_service import LegalKnowledgeService
from ..schemas.legal_knowledge import (
    TextExtractionRequest, ArticleExtractionRequest
)
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..utils.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/legal-knowledge", tags=["Legal Knowledge Processing"])


# ===========================================
# METADATA AND ARTICLE EXTRACTION ENDPOINTS
# ===========================================

@router.post("/law-sources/extract-metadata", response_model=ApiResponse)
async def extract_metadata(
    request: TextExtractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
 
    try:
        service = LegalKnowledgeService(db)
        result = await service.extract_law_source_metadata(
            text=request.text,
            existing_details=request.existing_details
        )
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(
                message=result["message"]
            )
    except Exception as e:
        logger.error(f"Failed to extract law source metadata: {str(e)}")
        return create_error_response(
            message=f"Failed to extract law source metadata: {str(e)}"
        )


@router.post("/articles/extract", response_model=ApiResponse)
async def extract_articles(
    request: ArticleExtractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
  
    try:
        service = LegalKnowledgeService(db)
        result = await service.extract_articles_from_text(
            text=request.text,
            law_source_id=request.law_source_id
        )
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(
                message=result["message"]
            )
    except Exception as e:
        logger.error(f"Failed to extract articles from text: {str(e)}")
        return create_error_response(
            message=f"Failed to extract articles from text: {str(e)}"
        )


# ===========================================
# HIERARCHICAL STRUCTURE ENDPOINTS
# ===========================================

@router.get("/documents/{law_source_id}/structure", response_model=ApiResponse)
async def get_document_structure(
    law_source_id: int = Path(..., gt=0, description="Law source ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
   
    try:
        service = LegalKnowledgeService(db)
        result = await service.get_document_structure(law_source_id=law_source_id)
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(
                message=result["message"]
            )
    except Exception as e:
        logger.error(f"Failed to get document structure: {str(e)}")
        return create_error_response(
            message=f"Failed to get document structure: {str(e)}"
        )


@router.post("/documents/{law_source_id}/validate-structure", response_model=ApiResponse)
async def validate_document_structure(
    law_source_id: int = Path(..., gt=0, description="Law source ID"),
    validate_numbering: bool = Query(default=True, description="Validate numbering continuity"),
    validate_hierarchy: bool = Query(default=True, description="Validate parent-child relationships"),
    detect_gaps: bool = Query(default=True, description="Detect missing elements"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    try:
        service = LegalKnowledgeService(db)
        result = await service.validate_document_structure(
            law_source_id=law_source_id,
            validate_numbering=validate_numbering,
            validate_hierarchy=validate_hierarchy,
            detect_gaps=detect_gaps
        )
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(
                message=result["message"]
            )
    except Exception as e:
        logger.error(f"Failed to validate document structure: {str(e)}")
        return create_error_response(
            message=f"Failed to validate document structure: {str(e)}"
        )
