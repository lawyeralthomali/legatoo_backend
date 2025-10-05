"""
Legal Document Processing API Router

This router provides API endpoints for processing legal documents
and extracting law sources and articles with high accuracy.
"""

import logging
import os
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Path, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal_knowledge_service import LegalKnowledgeService
from ..schemas.legal_knowledge import (
    ArabicDocumentProcessRequest, MultipleDocumentsProcessRequest,
    TextExtractionRequest, ArticleExtractionRequest
)
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..utils.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/legal-knowledge", tags=["Legal Document Processing"])


# ===========================================
# DOCUMENT PROCESSING ENDPOINTS
# ===========================================

@router.post("/documents/process", response_model=ApiResponse)
async def process_document(
    file: UploadFile = File(..., description="PDF or DOCX file to process"),
    name: Optional[str] = Form(None, description="Law source name"),
    type: Optional[str] = Form(None, description="Law source type (law, regulation, code, directive, decree)"),
    jurisdiction: Optional[str] = Form(None, description="Jurisdiction (e.g., المملكة العربية السعودية)"),
    issuing_authority: Optional[str] = Form(None, description="Issuing authority (e.g., وزارة العمل)"),
    issue_date: Optional[str] = Form(None, description="Issue date (YYYY-MM-DD format)"),
    last_update: Optional[str] = Form(None, description="Last update date (YYYY-MM-DD format)"),
    description: Optional[str] = Form(None, description="Law source description"),
    source_url: Optional[str] = Form(None, description="Source URL"),
    uploaded_by: Optional[int] = Form(None, description="User ID who uploaded the document"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a legal document and extract law sources and articles.
    
    This endpoint processes uploaded PDF or DOCX files containing legal content,
    automatically detecting law sources and extracting all articles.
    
    Args:
        file: Uploaded PDF or DOCX file
        name: Law source name (e.g., "نظام العمل السعودي")
        type: Law source type (law, regulation, code, directive, decree)
        jurisdiction: Jurisdiction (e.g., "المملكة العربية السعودية")
        issuing_authority: Issuing authority (e.g., "وزارة العمل")
        issue_date: Issue date in YYYY-MM-DD format
        last_update: Last update date in YYYY-MM-DD format
        description: Law source description
        source_url: Source URL
        uploaded_by: User ID who uploaded the document
        current_user: Current authenticated user
        
    Returns:
        ApiResponse with processed law source and articles data
    """
    try:
        # Validate file type
        if not file.filename:
            return create_error_response(
                message="No file provided"
            )
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.pdf', '.docx', '.doc']:
            return create_error_response(
                message="Invalid file type. Only PDF and DOCX files are supported"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/legal_documents"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        import uuid
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse law source details if provided
        parsed_law_source_details = None
        if any([name, type, jurisdiction, issuing_authority, issue_date, last_update, description, source_url]):
            parsed_law_source_details = {}
            
            # Validate law source type
            valid_types = ['law', 'regulation', 'code', 'directive', 'decree']
            if type and type not in valid_types:
                return create_error_response(
                    message=f"Invalid law source type. Must be one of: {', '.join(valid_types)}"
                )
            
            if name:
                parsed_law_source_details["name"] = name
            if type:
                parsed_law_source_details["type"] = type
            if jurisdiction:
                parsed_law_source_details["jurisdiction"] = jurisdiction
            if issuing_authority:
                parsed_law_source_details["issuing_authority"] = issuing_authority
            if issue_date:
                parsed_law_source_details["issue_date"] = issue_date
            if last_update:
                parsed_law_source_details["last_update"] = last_update
            if description:
                parsed_law_source_details["description"] = description
            if source_url:
                parsed_law_source_details["source_url"] = source_url
        
        # Process the document with hierarchical structure extraction
        service = LegalKnowledgeService(db)
        result = await service.process_arabic_legal_document_hierarchical(
            file_path=file_path,
            law_source_details=parsed_law_source_details,
            uploaded_by=uploaded_by or current_user.id
        )
        
        # Clean up uploaded file after processing
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up uploaded file {file_path}: {str(e)}")
        
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
        logger.error(f"Failed to process uploaded document: {str(e)}")
        return create_error_response(
            message=f"Failed to process uploaded document: {str(e)}"
        )


@router.post("/documents/process/batch", response_model=ApiResponse)
async def process_documents_batch(
    request: MultipleDocumentsProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process multiple legal documents in batch.
    
    This endpoint processes multiple PDF or DOCX files containing legal content,
    automatically detecting law sources and extracting articles from each document.
    
    Args:
        request: Multiple documents processing request
        current_user: Current authenticated user
        
    Returns:
        ApiResponse with processing results for all documents
    """
    try:
        service = LegalKnowledgeService(db)
        result = await service.process_multiple_arabic_documents(
            file_paths=request.file_paths,
            law_source_details=request.law_source_details,
            uploaded_by=request.uploaded_by or current_user.id
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
        logger.error(f"Failed to process multiple Arabic documents: {str(e)}")
        return create_error_response(
            message=f"Failed to process multiple Arabic documents: {str(e)}"
        )


@router.post("/law-sources/extract-metadata", response_model=ApiResponse)
async def extract_metadata(
    request: TextExtractionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Extract law source metadata from text.
    
    This endpoint analyzes legal text and extracts law source information
    such as name, type, issuing authority, dates, and description.
    
    Args:
        request: Text extraction request
        current_user: Current authenticated user
        
    Returns:
        ApiResponse with detected law source metadata
    """
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
    """
    Extract articles from legal text.
    
    This endpoint analyzes legal text and extracts all articles (مواد القانون),
    optionally creating them in the database if a law source ID is provided.
    
    Args:
        request: Article extraction request
        current_user: Current authenticated user
        
    Returns:
        ApiResponse with extracted articles
    """
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
    """
    Get the complete hierarchical structure of a processed document.
    
    This endpoint retrieves the full hierarchical structure (Chapters → Sections → Articles)
    of a previously processed legal document.
    
    Args:
        law_source_id: ID of the law source
        current_user: Current authenticated user
        
    Returns:
        ApiResponse with complete document structure
    """
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
    """
    Validate the hierarchical structure of a processed document.
    
    This endpoint validates the extracted hierarchical structure for consistency,
    numbering continuity, and completeness.
    
    Args:
        law_source_id: ID of the law source to validate
        validate_numbering: Whether to validate numbering continuity
        validate_hierarchy: Whether to validate parent-child relationships
        detect_gaps: Whether to detect missing elements
        current_user: Current authenticated user
        
    Returns:
        ApiResponse with validation results and suggestions
    """
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
