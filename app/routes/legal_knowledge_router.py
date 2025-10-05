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
    ✅ UPDATED: Upload and automatically parse legal law with full hierarchy extraction.
    
    This endpoint now uses the new Legal Laws Management system with:
    - SHA-256 file hashing for duplicate detection
    - Automatic hierarchy extraction (Branches → Chapters → Articles)
    - Knowledge chunk creation
    - Unified document management via KnowledgeDocument
    - Status tracking (raw → processed → indexed)
    
    **Returns:** Complete hierarchical tree with LawSource, branches, chapters, and articles.
    """
    try:
        # Validate file type
        if not file.filename:
            return create_error_response(message="No file provided")
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.pdf', '.docx', '.doc']:
            return create_error_response(
                message="Invalid file type. Only PDF and DOCX files are supported"
            )
        
        # Create uploads directory
        upload_dir = "uploads/legal_documents"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        import uuid
        import hashlib
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Calculate file hash for duplicate detection
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        file_hash = sha256_hash.hexdigest()
        
        # Validate and parse dates
        parsed_issue_date = None
        parsed_last_update = None
        
        if issue_date:
            try:
                from datetime import datetime
                parsed_issue_date = datetime.strptime(issue_date, "%Y-%m-%d").date()
            except ValueError:
                return create_error_response(message="Invalid issue_date format. Use YYYY-MM-DD")
        
        if last_update:
            try:
                from datetime import datetime
                parsed_last_update = datetime.strptime(last_update, "%Y-%m-%d").date()
            except ValueError:
                return create_error_response(message="Invalid last_update format. Use YYYY-MM-DD")
        
        # Prepare law source details
        if not name:
            name = os.path.splitext(file.filename)[0]  # Use filename if no name provided
        
        if not type:
            type = "law"  # Default to 'law' type
        
        # Validate law type
        valid_types = ['law', 'regulation', 'code', 'directive', 'decree']
        if type not in valid_types:
            return create_error_response(
                message=f"Invalid law source type. Must be one of: {', '.join(valid_types)}"
            )
        
        law_source_details = {
            "name": name,
            "type": type,
            "jurisdiction": jurisdiction,
            "issuing_authority": issuing_authority,
            "issue_date": parsed_issue_date,
            "last_update": parsed_last_update,
            "description": description,
            "source_url": source_url
        }
        
        # Use new Legal Laws Service for processing
        from ..services.legal_laws_service import LegalLawsService
        laws_service = LegalLawsService(db)
        
        result = await laws_service.upload_and_parse_law(
            file_path=file_path,
            file_hash=file_hash,
            original_filename=file.filename,
            law_source_details=law_source_details,
            uploaded_by=uploaded_by or current_user.sub
        )
        
        # File is kept for record (not deleted anymore for audit purposes)
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            # Clean up file on failure
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to clean up file {file_path}: {str(e)}")
            
            return create_error_response(
                message=result["message"],
                errors=result.get("errors", [])
            )
            
    except Exception as e:
        logger.error(f"Failed to process uploaded document: {str(e)}")
        
        # Clean up file on error
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        
        return create_error_response(
            message=f"Failed to process uploaded document: {str(e)}"
        )



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
