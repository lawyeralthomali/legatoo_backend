"""
Legal Laws Management API Router

This router provides comprehensive API endpoints for managing legal laws,
including upload, parsing, CRUD operations, and AI analysis.
"""

import logging
import os
import shutil
import hashlib
import uuid
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query, HTTPException, Path, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal_laws_service import LegalLawsService
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..utils.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/laws", tags=["Legal Laws Management"])


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# ===========================================
# LAW UPLOAD AND PARSING
# ===========================================

@router.post("/upload", response_model=ApiResponse)
async def upload_and_parse_law(
    law_name: str = Form(..., description="Name of the law"),
    law_type: str = Form(..., description="Type: law, regulation, code, directive, decree"),
    jurisdiction: Optional[str] = Form(None, description="Jurisdiction (e.g., المملكة العربية السعودية)"),
    issuing_authority: Optional[str] = Form(None, description="Issuing authority (e.g., وزارة العمل)"),
    issue_date: Optional[str] = Form(None, description="Issue date (YYYY-MM-DD format)"),
    last_update: Optional[str] = Form(None, description="Last update date (YYYY-MM-DD)"),
    description: Optional[str] = Form(None, description="Law description"),
    source_url: Optional[str] = Form(None, description="Source URL"),
    pdf_file: UploadFile = File(..., description="PDF file to upload and parse"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and automatically parse a legal law PDF.
    
    **Workflow:**
    1. Save PDF and calculate SHA-256 hash
    2. Create KnowledgeDocument with file hash (prevents duplicates)
    3. Create LawSource linked to KnowledgeDocument
    4. Parse PDF to extract hierarchy: Branches → Chapters → Articles
    5. Create KnowledgeChunks for each article
    6. Update status to 'processed'
    7. Return full hierarchical tree
    
    **Returns:**
    Complete law structure with branches, chapters, and articles.
    """
    try:
        # Validate file type
        if not pdf_file.filename:
            return create_error_response(message="No file provided")
        
        file_extension = os.path.splitext(pdf_file.filename)[1].lower()
        if file_extension not in ['.pdf', '.docx', '.doc']:
            return create_error_response(
                message="Invalid file type. Only PDF and DOCX files are supported"
            )
        
        # Validate law_type
        valid_types = ['law', 'regulation', 'code', 'directive', 'decree']
        if law_type not in valid_types:
            return create_error_response(
                message=f"Invalid law_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Create uploads directory
        upload_dir = "uploads/legal_documents"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
        
        # Calculate file hash for duplicate detection
        file_hash = calculate_file_hash(file_path)
        logger.info(f"Uploaded file hash: {file_hash}")
        
        # Parse dates if provided
        parsed_issue_date = None
        parsed_last_update = None
        
        if issue_date:
            try:
                parsed_issue_date = datetime.strptime(issue_date, "%Y-%m-%d").date()
            except ValueError:
                return create_error_response(message="Invalid issue_date format. Use YYYY-MM-DD")
        
        if last_update:
            try:
                parsed_last_update = datetime.strptime(last_update, "%Y-%m-%d").date()
            except ValueError:
                return create_error_response(message="Invalid last_update format. Use YYYY-MM-DD")
        
        # Prepare law source details
        law_source_details = {
            "name": law_name,
            "type": law_type,
            "jurisdiction": jurisdiction,
            "issuing_authority": issuing_authority,
            "issue_date": parsed_issue_date,
            "last_update": parsed_last_update,
            "description": description,
            "source_url": source_url
        }
        
        # Process the document
        service = LegalLawsService(db)
        result = await service.upload_and_parse_law(
            file_path=file_path,
            file_hash=file_hash,
            original_filename=pdf_file.filename,
            law_source_details=law_source_details,
            uploaded_by=current_user.sub
        )
        
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
                logger.warning(f"Failed to clean up file {file_path}: {e}")
            
            return create_error_response(
                message=result["message"],
                errors=result.get("errors", [])
            )
            
    except Exception as e:
        logger.error(f"Failed to upload and parse law: {str(e)}")
        
        # Clean up file on error
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        
        return create_error_response(
            message=f"Failed to upload and parse law: {str(e)}"
        )


# ===========================================
# LAW CRUD OPERATIONS
# ===========================================

@router.get("/", response_model=ApiResponse)
async def list_laws(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    law_type: Optional[str] = Query(None, description="Filter by type"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    status: Optional[str] = Query(None, description="Filter by status (raw, processed, indexed)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all laws with filtering and pagination.
    
    **Filters:**
    - name: Partial text match
    - law_type: Exact match (law, regulation, code, directive, decree)
    - jurisdiction: Partial match
    - status: Exact match (raw, processed, indexed)
    
    **Returns:**
    Paginated list of laws with metadata.
    """
    try:
        service = LegalLawsService(db)
        result = await service.list_laws(
            page=page,
            page_size=page_size,
            name_filter=name,
            type_filter=law_type,
            jurisdiction_filter=jurisdiction,
            status_filter=status
        )
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(message=result["message"])
            
    except Exception as e:
        logger.error(f"Failed to list laws: {str(e)}")
        return create_error_response(message=f"Failed to list laws: {str(e)}")


@router.get("/{law_id}/tree", response_model=ApiResponse)
async def get_law_tree(
    law_id: int = Path(..., gt=0, description="Law source ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve full hierarchical tree of a law.
    
    **Returns:**
    Complete law structure:
    ```
    LawSource
      └── LawBranch[]
            └── LawChapter[]
                  └── LawArticle[]
    ```
    
    Includes all metadata, content, and keywords.
    """
    try:
        service = LegalLawsService(db)
        result = await service.get_law_tree(law_id=law_id)
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(message=result["message"])
            
    except Exception as e:
        logger.error(f"Failed to get law tree: {str(e)}")
        return create_error_response(message=f"Failed to get law tree: {str(e)}")


@router.get("/{law_id}", response_model=ApiResponse)
async def get_law_metadata(
    law_id: int = Path(..., gt=0, description="Law source ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve LawSource metadata only (no hierarchy).
    
    **Returns:**
    LawSource basic information without branches/chapters/articles.
    """
    try:
        service = LegalLawsService(db)
        result = await service.get_law_metadata(law_id=law_id)
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(message=result["message"])
            
    except Exception as e:
        logger.error(f"Failed to get law metadata: {str(e)}")
        return create_error_response(message=f"Failed to get law metadata: {str(e)}")


@router.put("/{law_id}", response_model=ApiResponse)
async def update_law(
    law_id: int = Path(..., gt=0, description="Law source ID"),
    name: Optional[str] = Form(None, description="Updated law name"),
    law_type: Optional[str] = Form(None, description="Updated type"),
    jurisdiction: Optional[str] = Form(None, description="Updated jurisdiction"),
    issuing_authority: Optional[str] = Form(None, description="Updated issuing authority"),
    issue_date: Optional[str] = Form(None, description="Updated issue date (YYYY-MM-DD)"),
    last_update: Optional[str] = Form(None, description="Updated last update date (YYYY-MM-DD)"),
    description: Optional[str] = Form(None, description="Updated description"),
    source_url: Optional[str] = Form(None, description="Updated source URL"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update LawSource metadata fields.
    
    **Note:** Only updates metadata, does not re-parse the document.
    Use `/laws/{id}/reparse` to re-extract hierarchy from PDF.
    """
    try:
        # Validate law_type if provided
        if law_type:
            valid_types = ['law', 'regulation', 'code', 'directive', 'decree']
            if law_type not in valid_types:
                return create_error_response(
                    message=f"Invalid law_type. Must be one of: {', '.join(valid_types)}"
                )
        
        # Parse dates if provided
        parsed_issue_date = None
        parsed_last_update = None
        
        if issue_date:
            try:
                parsed_issue_date = datetime.strptime(issue_date, "%Y-%m-%d").date()
            except ValueError:
                return create_error_response(message="Invalid issue_date format. Use YYYY-MM-DD")
        
        if last_update:
            try:
                parsed_last_update = datetime.strptime(last_update, "%Y-%m-%d").date()
            except ValueError:
                return create_error_response(message="Invalid last_update format. Use YYYY-MM-DD")
        
        # Prepare update data
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if law_type is not None:
            update_data["type"] = law_type
        if jurisdiction is not None:
            update_data["jurisdiction"] = jurisdiction
        if issuing_authority is not None:
            update_data["issuing_authority"] = issuing_authority
        if parsed_issue_date is not None:
            update_data["issue_date"] = parsed_issue_date
        if parsed_last_update is not None:
            update_data["last_update"] = parsed_last_update
        if description is not None:
            update_data["description"] = description
        if source_url is not None:
            update_data["source_url"] = source_url
        
        if not update_data:
            return create_error_response(message="No fields provided to update")
        
        service = LegalLawsService(db)
        result = await service.update_law(law_id=law_id, update_data=update_data)
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(message=result["message"])
            
    except Exception as e:
        logger.error(f"Failed to update law: {str(e)}")
        return create_error_response(message=f"Failed to update law: {str(e)}")


@router.delete("/{law_id}", response_model=ApiResponse)
async def delete_law(
    law_id: int = Path(..., gt=0, description="Law source ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete LawSource and cascade delete all related data.
    
    **Cascade Deletes:**
    - All LawBranches
    - All LawChapters
    - All LawArticles
    - All linked KnowledgeChunks
    
    **Note:** The KnowledgeDocument (PDF file) is preserved for audit purposes.
    """
    try:
        service = LegalLawsService(db)
        result = await service.delete_law(law_id=law_id)
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(message=result["message"])
            
    except Exception as e:
        logger.error(f"Failed to delete law: {str(e)}")
        return create_error_response(message=f"Failed to delete law: {str(e)}")


# ===========================================
# LAW PROCESSING OPERATIONS
# ===========================================

@router.post("/{law_id}/reparse", response_model=ApiResponse)
async def reparse_law(
    law_id: int = Path(..., gt=0, description="Law source ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reparse uploaded PDF and regenerate hierarchy.
    
    **Workflow:**
    1. Delete existing branches, chapters, articles, and chunks
    2. Re-extract hierarchy from original PDF
    3. Recreate all records with updated parsing
    4. Update timestamps and status
    
    **Use Cases:**
    - Improved parsing algorithm
    - Fix extraction errors
    - Update after model changes
    """
    try:
        service = LegalLawsService(db)
        result = await service.reparse_law(law_id=law_id)
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(message=result["message"])
            
    except Exception as e:
        logger.error(f"Failed to reparse law: {str(e)}")
        return create_error_response(message=f"Failed to reparse law: {str(e)}")


@router.post("/{law_id}/analyze", response_model=ApiResponse)
async def analyze_law_with_ai(
    law_id: int = Path(..., gt=0, description="Law source ID"),
    generate_embeddings: bool = Query(True, description="Generate AI embeddings for articles"),
    extract_keywords: bool = Query(True, description="Extract keywords using AI"),
    update_existing: bool = Query(False, description="Update existing embeddings"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger AI analysis for law articles.
    
    **AI Operations:**
    - Generate embeddings for semantic search
    - Extract keywords from article content
    - Update `ai_processed_at` timestamps
    - Store embeddings in article and chunk records
    
    **Options:**
    - generate_embeddings: Create vector embeddings
    - extract_keywords: AI-powered keyword extraction
    - update_existing: Re-process already analyzed articles
    """
    try:
        service = LegalLawsService(db)
        result = await service.analyze_law_with_ai(
            law_id=law_id,
            generate_embeddings=generate_embeddings,
            extract_keywords=extract_keywords,
            update_existing=update_existing,
            processed_by=current_user.sub
        )
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(message=result["message"])
            
    except Exception as e:
        logger.error(f"Failed to analyze law with AI: {str(e)}")
        return create_error_response(message=f"Failed to analyze law with AI: {str(e)}")


# ===========================================
# STATISTICS AND UTILITIES
# ===========================================

@router.get("/{law_id}/statistics", response_model=ApiResponse)
async def get_law_statistics(
    law_id: int = Path(..., gt=0, description="Law source ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive statistics for a law.
    
    **Returns:**
    - Total branches, chapters, articles
    - Total chunks created
    - AI processing status
    - Verification statistics
    """
    try:
        service = LegalLawsService(db)
        result = await service.get_law_statistics(law_id=law_id)
        
        if result["success"]:
            return create_success_response(
                message=result["message"],
                data=result["data"]
            )
        else:
            return create_error_response(message=result["message"])
            
    except Exception as e:
        logger.error(f"Failed to get law statistics: {str(e)}")
        return create_error_response(message=f"Failed to get law statistics: {str(e)}")
