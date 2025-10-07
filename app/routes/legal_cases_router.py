"""
Legal Cases Router

API endpoints for ingesting and managing historical legal cases.
Follows clean architecture with thin routes delegating to service layer.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal_case_ingestion_service import LegalCaseIngestionService
from ..services.legal_case_service import LegalCaseService
from ..utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/legal-cases",
    tags=["Legal Cases"]
)


@router.post("/upload", response_model=None)
async def upload_legal_case(
    # File upload
    file: UploadFile = File(..., description="PDF, DOCX, or TXT file containing the legal case"),
    
    # Case metadata
    case_number: Optional[str] = Form(None, description="Case reference number (e.g., 123/2024)"),
    title: str = Form(..., description="Case title"),
    description: Optional[str] = Form(None, description="Brief description of the case"),
    jurisdiction: Optional[str] = Form(None, description="Legal jurisdiction (e.g., الرياض)"),
    court_name: Optional[str] = Form(None, description="Name of the court"),
    decision_date: Optional[str] = Form(None, description="Date of decision (YYYY-MM-DD)"),
    case_type: Optional[str] = Form(None, description="Type: مدني, جنائي, تجاري, عمل, إداري"),
    court_level: Optional[str] = Form(None, description="Level: ابتدائي, استئناف, تمييز, عالي"),
    
    # Dependencies
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Upload and ingest a historical legal case from PDF, DOCX, or TXT file.
    
    This endpoint:
    1. Saves the uploaded file and creates a KnowledgeDocument record
    2. Extracts text from the file
    3. Segments the text into logical sections (summary, facts, arguments, ruling, legal_basis)
    4. Creates LegalCase and CaseSection records in the database
    
    **Supported file formats**: PDF, DOCX, TXT
    
    **Required fields**: file, title
    
    **Arabic section detection**:
    - ملخص → summary
    - الوقائع → facts
    - الحجج → arguments
    - الحكم → ruling
    - الأساس القانوني → legal_basis
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "No file provided",
                    "data": None,
                    "errors": [{"field": "file", "message": "File is required"}]
                }
            )
        
        file_extension = file.filename.lower().split('.')[-1]
        if file_extension not in ['pdf', 'docx', 'doc', 'txt']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Invalid file format. Only PDF, DOCX, and TXT are supported.",
                    "data": None,
                    "errors": [{"field": "file", "message": "Only PDF, DOCX, and TXT files are supported"}]
                }
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Uploaded file is empty",
                    "data": None,
                    "errors": [{"field": "file", "message": "File is empty"}]
                }
            )
        
        # Prepare case metadata
        case_metadata = {
            'case_number': case_number,
            'title': title,
            'description': description,
            'jurisdiction': jurisdiction,
            'court_name': court_name,
            'decision_date': decision_date,
            'case_type': case_type,
            'court_level': court_level
        }
        
        # Initialize ingestion service
        ingestion_service = LegalCaseIngestionService(db)
        
        # Ingest the case
        result = await ingestion_service.ingest_legal_case(
            file_content=file_content,
            filename=file.filename,
            case_metadata=case_metadata,
            uploaded_by=current_user.sub
        )
        
        if result['success']:
            return {
                "success": True,
                "message": result['message'],
                "data": result['data'],
                "errors": []
            }
        else:
            # Ingestion failed - return 400 or 422 depending on the error
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "success": False,
                    "message": result['message'],
                    "data": None,
                    "errors": [{"field": None, "message": result['message']}]
                }
            )
    
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": str(e),
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )
    
    except Exception as e:
        logger.exception("Unexpected error during legal case upload")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Failed to upload legal case: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.get("/", response_model=None)
async def list_legal_cases(
    skip: int = 0,
    limit: int = 50,
    jurisdiction: Optional[str] = None,
    case_type: Optional[str] = None,
    court_level: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all legal cases with filtering and pagination.
    
    **Query parameters**:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum records to return (default: 50)
    - jurisdiction: Filter by jurisdiction
    - case_type: Filter by case type (مدني, جنائي, تجاري, عمل, إداري)
    - court_level: Filter by court level (ابتدائي, استئناف, تمييز, عالي)
    - status: Filter by status (raw, processed, indexed)
    - search: Search in case title or case number
    """
    # Delegate to service layer
    service = LegalCaseService(db)
    result = await service.list_legal_cases(
        skip=skip,
        limit=limit,
        jurisdiction=jurisdiction,
        case_type=case_type,
        court_level=court_level,
        status=status,
        search=search
    )
    
    # Return service response directly (already in correct format)
    return result


@router.get("/{case_id}", response_model=None)
async def get_legal_case(
    case_id: int,
    include_sections: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get detailed information about a specific legal case.
    
    **Parameters**:
    - case_id: ID of the legal case
    - include_sections: Include case sections in response (default: true)
    """
    # Delegate to service layer
    service = LegalCaseService(db)
    result = await service.get_legal_case(
        case_id=case_id,
        include_sections=include_sections
    )
    
    # Return service response directly
    return result


@router.put("/{case_id}", response_model=None)
async def update_legal_case(
    case_id: int,
    case_number: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    jurisdiction: Optional[str] = Form(None),
    court_name: Optional[str] = Form(None),
    decision_date: Optional[str] = Form(None),
    case_type: Optional[str] = Form(None),
    court_level: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update legal case metadata.
    
    **Note**: This endpoint updates only the case metadata, not the sections.
    """
    # Delegate to service layer
    service = LegalCaseService(db)
    result = await service.update_legal_case(
        case_id=case_id,
        case_number=case_number,
        title=title,
        description=description,
        jurisdiction=jurisdiction,
        court_name=court_name,
        decision_date=decision_date,
        case_type=case_type,
        court_level=court_level
    )
    
    # Return service response directly
    return result


@router.delete("/{case_id}", response_model=None)
async def delete_legal_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a legal case and all its sections.
    
    **Warning**: This action is permanent and cannot be undone.
    The associated KnowledgeDocument will NOT be deleted (only the case link).
    """
    # Delegate to service layer
    service = LegalCaseService(db)
    result = await service.delete_legal_case(case_id)
    
    # Return service response directly
    return result


@router.get("/{case_id}/sections", response_model=None)
async def get_case_sections(
    case_id: int,
    section_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all sections of a legal case.
    
    **Parameters**:
    - case_id: ID of the legal case
    - section_type: Optional filter by section type (summary, facts, arguments, ruling, legal_basis)
    """
    # Delegate to service layer
    service = LegalCaseService(db)
    result = await service.get_case_sections(
        case_id=case_id,
        section_type=section_type
    )
    
    # Return service response directly
    return result

