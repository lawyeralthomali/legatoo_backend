"""
Legal Cases Router

API endpoints for ingesting and managing historical legal cases.
Follows clean architecture with thin routes delegating to service layer.
"""

import logging
import json
from typing import Optional, List
from urllib.parse import quote
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal.ingestion.legal_case_ingestion_service import LegalCaseIngestionService
from ..services.legal.knowledge.legal_case_service import LegalCaseService
from ..services.legal.analysis.case_analysis_service import CaseAnalysisService
from ..services.legal.analysis.contract_analysis_service import ContractAnalysisService
from ..services.case_analysis.case_analysis_history_service import CaseAnalysisHistoryService
from ..services.user_management.profile_service import ProfileService
from ..utils.auth import get_current_user, get_current_user_id, TokenData
from ..models.user import User
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from fastapi.responses import StreamingResponse

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


@router.post("/upload-json", response_model=ApiResponse)
async def upload_case_json(
    json_file: UploadFile = File(..., description="JSON file containing legal case structure"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a JSON file containing extracted legal case structure and save to database.
    
    **JSON Format Expected (Legal Case Structure):**
    ```json
    {
      "legal_cases": [
        {
          "case_number": "123/2024",
          "title": "قضية عمالية - إنهاء خدمات",
          "description": "نزاع حول إنهاء خدمات عامل بدون مبرر",
          "jurisdiction": "الرياض",
          "court_name": "المحكمة العمالية بالرياض",
          "decision_date": "2024-01-15",
          "case_type": "عمل",
          "court_level": "ابتدائي",
          "sections": [
            {
              "section_type": "summary",
              "content": "ملخص القضية: نزاع بين عامل وصاحب عمل حول..."
            },
            {
              "section_type": "facts",
              "content": "وقائع القضية: تقدم العامل بشكوى ضد صاحب العمل..."
            },
            {
              "section_type": "arguments",
              "content": "حجج الأطراف: ادعى العامل أن... بينما رد صاحب العمل..."
            },
            {
              "section_type": "ruling",
              "content": "الحكم: حكمت المحكمة بإلزام صاحب العمل..."
            },
            {
              "section_type": "legal_basis",
              "content": "الأساس القانوني: استندت المحكمة إلى المادة 74 من نظام العمل..."
            }
          ]
        }
      ],
      "processing_report": {
        "total_cases": 1,
        "warnings": [],
        "errors": [],
        "suggestions": ["تحقق من اكتمال البيانات"]
      }
    }
    ```
    
    **Important Notes:**
    - This is for **LEGAL CASES**, not laws
    - `case_type` must be one of: 'مدني', 'جنائي', 'تجاري', 'عمل', 'إداري'
    - `court_level` must be one of: 'ابتدائي', 'استئناف', 'تمييز', 'عالي'
    - `section_type` must be one of: 'summary', 'facts', 'arguments', 'ruling', 'legal_basis'
    - `decision_date` should be in YYYY-MM-DD format
    
    **Workflow:**
    1. Validate JSON file format
    2. Parse legal case structure from JSON
    3. Create KnowledgeDocument (no file, just metadata)
    4. Create LegalCase with extracted metadata
    5. Create CaseSection for each section (summary, facts, arguments, ruling, legal_basis)
    6. Create KnowledgeChunks for each section
    7. Return success with statistics
    
    **Returns:**
    Success message with processing statistics.
    """
    try:
        # Validate file type
        if not json_file.filename:
            return create_error_response(message="No file provided")
        
        if not json_file.filename.lower().endswith('.json'):
            return create_error_response(
                message="Invalid file type. Only JSON files are supported"
            )
        
        # Read and parse JSON content
        try:
            content = await json_file.read()
            json_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            return create_error_response(
                message=f"Invalid JSON format: {str(e)}"
            )
        except Exception as e:
            return create_error_response(
                message=f"Failed to read JSON file: {str(e)}"
            )
        
        # Validate JSON structure
        if "legal_cases" not in json_data or not json_data["legal_cases"]:
            return create_error_response(
                message="Invalid JSON structure. Missing 'legal_cases' array"
            )
        
        # Process the JSON data using LegalCaseService
        service = LegalCaseService(db)
        result = await service.upload_json_case_structure(
            json_data=json_data,
            uploaded_by=1  # Use hardcoded user ID 1
        )
        
        if result["success"]:
            return create_success_response(
                message=f"✅ Successfully processed JSON case structure: {result['message']}",
                data=result["data"]
            )
        else:
            return create_error_response(
                message=f"❌ Failed to process JSON case structure: {result['message']}",
                errors=result.get("errors", [])
            )
            
    except Exception as e:
        logger.error(f"Failed to upload JSON case structure: {str(e)}")
        return create_error_response(
            message=f"Failed to upload JSON case structure: {str(e)}"
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


@router.post("/analysis", response_model=None)
async def analyze_legal_case(
    files: List[UploadFile] = File(..., description="Legal case files (PDF, DOCX, TXT)"),
    analysis_type: str = Form(..., description="Type of analysis: 'case-analysis' or 'contract-review'"),
    lawsuit_type: str = Form(..., description="Type of lawsuit (e.g., commercial, labor, civil)"),
    result_seeking: str = Form(..., description="What the user wants to achieve from the analysis"),
    user_context: Optional[str] = Form(None, description="Additional context or information"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Analyze legal case files using AI (Gemini) according to Saudi Arabian law.
    Provides comprehensive analysis suitable for both lawyers and users.
    """
    try:
        valid_analysis_types = ["case-analysis", "contract-review"]
        if analysis_type not in valid_analysis_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": f"Invalid analysis_type. Must be one of: {', '.join(valid_analysis_types)}",
                    "data": None,
                    "errors": [{"field": "analysis_type", "message": f"Must be one of: {', '.join(valid_analysis_types)}"}]
                }
            )
        
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "At least one file is required",
                    "data": None,
                    "errors": [{"field": "files", "message": "At least one file is required"}]
                }
            )
        
        valid_extensions = ['pdf', 'docx', 'doc', 'txt']
        uploaded_files = []
        
        for file in files:
            if not file.filename:
                continue
                
            file_extension = file.filename.lower().split('.')[-1]
            if file_extension not in valid_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": f"Invalid file type: {file.filename}. Only PDF, DOCX, DOC, and TXT are supported.",
                        "data": None,
                        "errors": [{"field": "files", "message": f"Invalid file type: {file.filename}"}]
                    }
                )
            
            file_content = await file.read()
            file_size_mb = len(file_content) / (1024 * 1024)
            
            if file_size_mb > 20:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": f"File {file.filename} is too large ({file_size_mb:.1f}MB). Maximum size is 20MB.",
                        "data": None,
                        "errors": [{"field": "files", "message": f"File {file.filename} exceeds size limit"}]
                    }
                )
            
            uploaded_files.append({
                "filename": file.filename,
                "content": file_content,
                "size": file_size_mb
            })
        
        if not uploaded_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "No valid files provided",
                    "data": None,
                    "errors": [{"field": "files", "message": "No valid files provided"}]
                }
            )
        
        primary_file = uploaded_files[0]
        analysis_service = CaseAnalysisService()
        
        logger.info(f"Starting analysis for file: {primary_file['filename']}, type: {analysis_type}")
        
        result = await analysis_service.analyze_case(
            file_content=primary_file["content"],
            filename=primary_file["filename"],
            analysis_type=analysis_type,
            lawsuit_type=lawsuit_type,
            result_seeking=result_seeking,
            user_context=user_context
        )
        
        logger.info(f"Analysis result - success: {result.get('success')}, has data: {'data' in result}")
        
        if result.get("success") and result.get("data"):
            # Save analysis to history (non-blocking - don't fail request if save fails)
            # This is wrapped in try-except to ensure analysis is always returned
            try:
                # Get user's profile ID
                profile_service = ProfileService(db)
                profile = await profile_service.get_profile_response_by_id(current_user.sub)
                
                if profile:
                    history_service = CaseAnalysisHistoryService(db)
                    
                    # Prepare additional files info
                    additional_files_info = None
                    if len(uploaded_files) > 1:
                        additional_files_info = [
                            {"filename": f["filename"], "size_mb": f["size"]}
                            for f in uploaded_files[1:]
                        ]
                        if "additional_files" not in result["data"]:
                            result["data"]["additional_files"] = additional_files_info
                    
                    # Extract analysis data safely
                    analysis_obj = result["data"].get("analysis", {})
                    if not isinstance(analysis_obj, dict):
                        analysis_obj = {}
                    
                    # Get raw_response - it might be in analysis_data or directly in result["data"]
                    raw_response = result["data"].get("raw_response")
                    if not raw_response:
                        raw_response = analysis_obj.get("raw_response") or analysis_obj.get("full_analysis")
                    
                    # Get risk score and label safely
                    risk_score = analysis_obj.get("risk_score") if isinstance(analysis_obj, dict) else None
                    risk_label = analysis_obj.get("risk_label") if isinstance(analysis_obj, dict) else None
                    
                    # Save to history - use separate try-except for database operations
                    try:
                        saved_analysis = await history_service.save_analysis(
                            user_id=profile.id,  # Profile ID
                            filename=primary_file["filename"],
                            file_size_mb=primary_file["size"],
                            analysis_type=analysis_type,
                            lawsuit_type=lawsuit_type,
                            result_seeking=result_seeking,
                            user_context=user_context,
                            analysis_data=result["data"],  # Full data structure
                            risk_score=risk_score,
                            risk_label=risk_label,
                            raw_response=raw_response,
                            additional_files=additional_files_info
                        )
                        
                        # Add analysis ID to response only if save succeeded
                        if saved_analysis and saved_analysis.id:
                            result["data"]["analysis_id"] = saved_analysis.id
                            logger.info(f"Analysis saved to history with ID: {saved_analysis.id}")
                    except Exception as db_error:
                        # Database save failed - log but continue
                        logger.error(f"Database save failed for analysis: {db_error}", exc_info=True)
                else:
                    logger.warning(f"Profile not found for user {current_user.sub}, skipping history save")
            except Exception as e:
                # Log error but don't fail the request - analysis should still be returned
                logger.error(f"Failed to save analysis to history: {e}", exc_info=True)
                # Continue - don't raise exception, just log
            
            # Return analysis result regardless of history save status
            # This ensures the user always gets their analysis even if history save fails
            logger.info(f"Returning analysis result for {primary_file['filename']}")
            return {
                "success": True,
                "message": result.get("message", "Case analysis completed successfully"),
                "data": result.get("data"),
                "errors": []
            }
        else:
            error_message = result.get("message", "Analysis failed")
            logger.error(f"Analysis failed: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": error_message,
                    "data": None,
                    "errors": [{"field": None, "message": error_message}]
                }
            )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception("Unexpected error during legal case analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Failed to analyze legal case: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.get("/analysis/history", response_model=None)
async def get_analysis_history(
    skip: int = 0,
    limit: int = 100,
    analysis_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get user's case analysis history."""
    try:
        # Get user's profile ID
        profile_service = ProfileService(db)
        profile = await profile_service.get_profile_response_by_id(current_user.sub)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Profile not found",
                    "data": None,
                    "errors": [{"field": "profile", "message": "User profile not found"}]
                }
            )
        
        history_service = CaseAnalysisHistoryService(db)
        result = await history_service.get_user_analyses(
            user_id=profile.id,
            skip=skip,
            limit=limit,
            analysis_type=analysis_type
        )
        
        return {
            "success": True,
            "message": "Analysis history retrieved successfully",
            "data": result,
            "errors": []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving analysis history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Failed to retrieve analysis history: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.get("/analysis/{analysis_id}", response_model=None)
async def get_analysis_by_id(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get a specific analysis by ID."""
    try:
        # Get user's profile ID
        profile_service = ProfileService(db)
        profile = await profile_service.get_profile_response_by_id(current_user.sub)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Profile not found",
                    "data": None,
                    "errors": [{"field": "profile", "message": "User profile not found"}]
                }
            )
        
        history_service = CaseAnalysisHistoryService(db)
        analysis = await history_service.get_analysis_by_id(analysis_id, profile.id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Analysis not found",
                    "data": None,
                    "errors": [{"field": "analysis_id", "message": "Analysis not found"}]
                }
            )
        
        return {
            "success": True,
            "message": "Analysis retrieved successfully",
            "data": analysis.to_dict(),
            "errors": []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error retrieving analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Failed to retrieve analysis: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.get("/analysis/{analysis_id}/download", response_model=None)
async def download_analysis_pdf(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Download analysis as PDF."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_RIGHT, TA_LEFT
        from io import BytesIO
        import json
        
        # Get user's profile ID
        profile_service = ProfileService(db)
        profile = await profile_service.get_profile_response_by_id(current_user.sub)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Profile not found",
                    "data": None,
                    "errors": []
                }
            )
        
        history_service = CaseAnalysisHistoryService(db)
        analysis = await history_service.get_analysis_by_id(analysis_id, profile.id)
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Analysis not found",
                    "data": None,
                    "errors": []
                }
            )
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create PDF document with RTL-friendly margins
        # For RTL text, we want text to start from right edge
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            topMargin=0.5*inch, 
            bottomMargin=0.5*inch,
            leftMargin=0.75*inch,   # Standard left margin
            rightMargin=0.75*inch   # Standard right margin (text aligns to this for RTL)
        )
        styles = getSampleStyleSheet()
        
        # Register Arabic font - always use Arabic as default
        arabic_font_name = None
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            import os
            import platform
            from pathlib import Path
            
            # First, try to load font from app/fonts directory (bundled with app)
            app_dir = Path(__file__).parent.parent  # Go up from routes/ to app/
            fonts_dir = app_dir / "fonts"
            
            # Common Arabic font filenames to try
            font_files = [
                "NotoSansArabic-Regular.ttf",
                "NotoSansArabic.ttf",
                "DejaVuSans.ttf",
                "arial-unicode-ms.ttf",
                "ARIALUNI.TTF",
            ]
            
            # Try bundled fonts first
            for font_file in font_files:
                font_path = fonts_dir / font_file
                if font_path.exists():
                    try:
                        font_name = "ArabicFont"  # Use consistent name
                        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
                        arabic_font_name = font_name
                        logger.info(f"Registered bundled Arabic font: {font_name} from {font_path}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to register bundled font {font_file}: {e}")
                        continue
            
            # If no bundled font, try system fonts
            if not arabic_font_name:
                system = platform.system()
                
                # Define font paths based on operating system
                if system == "Windows":
                    font_paths_to_try = [
                        ('ArabicFont', 'C:/Windows/Fonts/DejaVuSans.ttf'),
                        ('ArabicFont', 'C:/Windows/Fonts/ARIALUNI.TTF'),
                        ('ArabicFont', 'C:/Windows/Fonts/arialuni.ttf'),
                    ]
                elif system == "Linux":
                    font_paths_to_try = [
                        ('ArabicFont', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
                        ('ArabicFont', '/usr/share/fonts/TTF/DejaVuSans.ttf'),
                        ('ArabicFont', '/usr/share/fonts/DejaVuSans.ttf'),
                    ]
                else:  # macOS or other
                    font_paths_to_try = [
                        ('ArabicFont', '/System/Library/Fonts/DejaVuSans.ttf'),
                        ('ArabicFont', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'),
                    ]
                
                for font_name, font_path in font_paths_to_try:
                    try:
                        if os.path.exists(font_path):
                            pdfmetrics.registerFont(TTFont(font_name, font_path))
                            arabic_font_name = font_name
                            logger.info(f"Registered system Arabic font: {font_name} from {font_path}")
                            break
                    except Exception as e:
                        logger.warning(f"Failed to register {font_name} from {font_path}: {e}")
                        continue
            
            if not arabic_font_name:
                logger.error("CRITICAL: No Arabic-supporting font found. Arabic text will display as rectangles in PDF.")
                logger.error(f"Please download Noto Sans Arabic and place it in: {fonts_dir}")
        except ImportError:
            logger.error("Cannot register custom fonts - reportlab.pdfbase not available")
        
        # Helper function to detect Arabic text
        def contains_arabic(text):
            if not text:
                return False
            text_str = str(text)
            # Check for Arabic Unicode range
            return any('\u0600' <= char <= '\u06FF' for char in text_str)
        
        # Always use Arabic font as default (or Helvetica as fallback)
        base_font = arabic_font_name if arabic_font_name else 'Helvetica'
        if not arabic_font_name:
            logger.warning("Using Helvetica as fallback - Arabic text may not display correctly!")
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=base_font,  # Always use Arabic font
            fontSize=18,
            textColor='#1f2937',
            spaceAfter=12,
            alignment=TA_RIGHT  # Right-align for Arabic support
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=base_font,  # Always use Arabic font
            fontSize=14,
            textColor='#374151',
            spaceAfter=8,
            spaceBefore=12,
            alignment=TA_RIGHT  # Right-align for Arabic support
        )
        
        # Default style - always use Arabic font and right alignment
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=base_font,  # Always use Arabic font
            fontSize=10,
            textColor='#4b5563',
            spaceAfter=6,
            alignment=TA_RIGHT,  # Right-align as default for Arabic support
            leading=14
        )
        
        # Arabic-specific style (same as normal now since we always use Arabic)
        arabic_normal_style = normal_style
        
        # Get analysis data
        analysis_data = analysis.analysis_data
        sections = analysis_data.get("analysis", {}).get("sections", {})
        
        # Import Arabic text processing libraries
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            ARABIC_PROCESSING_AVAILABLE = True
        except ImportError:
            ARABIC_PROCESSING_AVAILABLE = False
            logger.warning("arabic-reshaper or python-bidi not available. Arabic text may not connect properly.")
        
        # Helper function to process Arabic text (reshape and BiDi)
        def process_arabic_text(text):
            """Process Arabic text to ensure proper character connection and RTL display.
            Adds RTL marks to ensure text flows from right to left and aligns properly."""
            if not text or not ARABIC_PROCESSING_AVAILABLE:
                return str(text) if text else ""
            
            text_str = str(text)
            
            # Check if text contains Arabic characters
            if not contains_arabic(text_str):
                return text_str  # Return as-is if no Arabic
            
            try:
                # Reshape Arabic text so characters connect properly
                reshaped_text = arabic_reshaper.reshape(text_str)
                
                # Apply bidirectional algorithm for proper RTL display
                bidi_text = get_display(reshaped_text)
                
                # Add RTL override marks to ensure proper right-to-left flow
                # \u202E = Right-to-Left Override (forces RTL direction)
                # \u202C = Pop Directional Formatting (ends RTL override)
                # This ensures text starts from right and flows leftward
                rtl_text = '\u202E' + bidi_text + '\u202C'
                
                return rtl_text
            except Exception as e:
                logger.warning(f"Failed to process Arabic text: {e}")
                return text_str  # Fallback to original text
        
        # Helper function to safely escape HTML
        def escape_html(text):
            if not text:
                return ""
            return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Helper function to convert markdown to ReportLab HTML format
        def markdown_to_reportlab(text):
            """Convert markdown formatting to ReportLab Paragraph-compatible HTML.
            Preserves line breaks and formatting for proper RTL alignment.
            This matches the frontend's <pre> whitespace-pre-wrap display."""
            if not text:
                return ""
            
            import re
            text_str = str(text)
            
            # Convert markdown bold **text** to <b>text</b> (handle multiline properly)
            # Use non-greedy matching to handle multiple bold sections
            text_str = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', text_str)
            
            # Convert markdown bullets * item or - item to bullet points
            # For RTL Arabic, bullet should be on the right, so we'll use • 
            text_str = re.sub(r'^\s*[-*]\s+', '• ', text_str, flags=re.MULTILINE)
            
            # Preserve numbered lists (1. 2. etc.) - keep as is for RTL
            # They're already formatted correctly
            
            # Convert line breaks to <br/> tags for ReportLab
            # Preserve empty lines as single <br/> to maintain spacing
            lines = text_str.split('\n')
            formatted_lines = []
            
            for i, line in enumerate(lines):
                if not line.strip():
                    # Empty line - add break (but not at start/end if not needed)
                    if formatted_lines:  # Only add if we have content before
                        formatted_lines.append("<br/>")
                else:
                    # Non-empty line - add it with proper formatting
                    formatted_lines.append(line)
            
            # Join with <br/> tags to preserve line structure
            return '<br/>'.join(formatted_lines)
        
        # Helper function to prepare text for PDF (process Arabic + convert markdown + escape HTML)
        def prepare_text_for_pdf(text):
            """Process Arabic text, convert markdown, and escape HTML for safe PDF rendering.
            Returns properly formatted text for ReportLab Paragraph with RTL support."""
            if not text:
                return ""
            
            # First process Arabic (reshape + bidi) - this handles character connection and RTL direction
            processed_text = process_arabic_text(text)
            
            # Convert markdown to ReportLab HTML format
            markdown_processed = markdown_to_reportlab(processed_text)
            
            # Escape HTML entities but preserve ReportLab formatting tags
            # Escape & first, then < and >
            markdown_processed = markdown_processed.replace("&", "&amp;")
            # Now escape < and > that are NOT part of our formatting tags
            import re
            # Protect our formatting tags first
            protected = []
            tag_pattern = r'(<(?:b|br|/b|br/)[^>]*>)'
            for match in re.finditer(tag_pattern, markdown_processed, re.IGNORECASE):
                placeholder = f"__TAG_{len(protected)}__"
                protected.append((placeholder, match.group(0)))
                markdown_processed = markdown_processed.replace(match.group(0), placeholder, 1)
            
            # Escape remaining < and >
            markdown_processed = markdown_processed.replace("<", "&lt;").replace(">", "&gt;")
            
            # Restore protected tags
            for placeholder, tag in protected:
                markdown_processed = markdown_processed.replace(placeholder, tag)
            
            return markdown_processed
        
        # Helper function to choose appropriate style based on content
        # Always use Arabic font style (default is Arabic)
        def get_paragraph_style(text):
            return arabic_normal_style  # Always use Arabic style
        
        # Build PDF content - match frontend display order exactly
        story = []
        
        # Title
        story.append(Paragraph(f"<b>Legal Case Analysis Report</b>", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # File Information (process Arabic text in filename and labels)
        filename_display = prepare_text_for_pdf(analysis.filename)
        analysis_type_display = prepare_text_for_pdf(analysis.analysis_type)
        lawsuit_type_display = prepare_text_for_pdf(analysis.lawsuit_type)
        risk_label_display = prepare_text_for_pdf(analysis.risk_label) if analysis.risk_label else ""
        
        story.append(Paragraph(f"<b>File:</b> {filename_display}", normal_style))
        story.append(Paragraph(f"<b>Analysis Type:</b> {analysis_type_display}", normal_style))
        story.append(Paragraph(f"<b>Lawsuit Type:</b> {lawsuit_type_display}", normal_style))
        story.append(Paragraph(f"<b>Date:</b> {analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        if analysis.risk_score is not None:
            story.append(Paragraph(f"<b>Risk Score:</b> {analysis.risk_score}% ({risk_label_display})", normal_style))
        story.append(Spacer(1, 0.2*inch))
        
        # IMPORTANT: Match frontend display order exactly
        # Frontend shows: formatted_analysis first, then sections
        
        # 1. Full Analysis Text (formatted_analysis) - shown FIRST like frontend
        # Frontend displays this in <pre> with whitespace-pre-wrap, preserving exact formatting
        formatted_analysis_text = None
        if sections.get("formatted_analysis"):
            formatted_analysis_text = sections.get("formatted_analysis")
        elif analysis_data.get("formatted_analysis"):
            formatted_analysis_text = analysis_data.get("formatted_analysis")
        
        if formatted_analysis_text:
            story.append(Paragraph("<b>Complete Analysis</b>", heading_style))
            full_text = str(formatted_analysis_text)
            
            # Frontend displays this in <pre> with whitespace-pre-wrap, preserving exact formatting
            # We need to preserve line breaks and structure exactly as frontend shows it
            # Split the text by lines to preserve structure
            lines = full_text.split('\n')
            
            current_section = []
            for line in lines:
                line_stripped = line.strip()
                
                # Handle markdown headers
                if line_stripped.startswith('##'):
                    # Add any accumulated content first
                    if current_section:
                        section_text = '\n'.join(current_section)
                        if section_text.strip():
                            story.append(Paragraph(prepare_text_for_pdf(section_text), normal_style))
                            story.append(Spacer(1, 0.05*inch))
                        current_section = []
                    
                    # Extract header text (remove ##, ###, ####)
                    header_text = re.sub(r'^#+\s*', '', line_stripped)
                    if header_text:
                        # Determine header style based on level
                        if line_stripped.startswith('####'):
                            story.append(Paragraph(f"<b>{prepare_text_for_pdf(header_text)}</b>", normal_style))
                        elif line_stripped.startswith('###'):
                            story.append(Paragraph(f"<b>{prepare_text_for_pdf(header_text)}</b>", heading_style))
                        else:  # ##
                            story.append(Paragraph(f"<b>{prepare_text_for_pdf(header_text)}</b>", title_style))
                        story.append(Spacer(1, 0.1*inch))
                else:
                    # Regular content line - preserve it
                    current_section.append(line)
            
            # Add remaining content
            if current_section:
                section_text = '\n'.join(current_section)
                if section_text.strip():
                    story.append(Paragraph(prepare_text_for_pdf(section_text), normal_style))
            
            story.append(Spacer(1, 0.2*inch))
        
        # 2. Individual Sections - Only display if formatted_analysis is NOT available
        # Frontend shows formatted_analysis first (which contains everything), 
        # then individual sections only if formatted_analysis is not present
        # Since formatted_analysis contains all content, we skip individual sections
        
        # Frontend shows formatted_analysis first, then ALSO shows individual sections below.
        # We match this behavior - show both formatted_analysis AND individual sections
        # Individual sections will only display if they have content (not empty strings)
        
        # Show individual sections (like frontend does)
        # These provide structured breakdown even if formatted_analysis exists
        
        # Executive Summary
        if sections.get("executive_summary") and sections.get("executive_summary").strip():
            story.append(Paragraph("<b>1. Executive Summary</b>", heading_style))
            summary_text = sections["executive_summary"]
            story.append(Paragraph(prepare_text_for_pdf(summary_text), get_paragraph_style(summary_text)))
            story.append(Spacer(1, 0.1*inch))
        
        # Legal Analysis sections
        if sections.get("legal_analysis") or sections.get("legal_status"):
            story.append(Paragraph("<b>2. Detailed Legal Analysis</b>", heading_style))
            
            if sections.get("legal_status") and sections.get("legal_status").strip():
                story.append(Paragraph("<b>a. Current Legal Status</b>", normal_style))
                status_text = sections["legal_status"]
                story.append(Paragraph(prepare_text_for_pdf(status_text), get_paragraph_style(status_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("weak_points") and sections.get("weak_points").strip():
                story.append(Paragraph("<b>b. Weak Points in the Case</b>", normal_style))
                weak_points_text = sections["weak_points"]
                story.append(Paragraph(prepare_text_for_pdf(weak_points_text), get_paragraph_style(weak_points_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("strong_points") and sections.get("strong_points").strip():
                story.append(Paragraph("<b>c. Strong Points in the Case</b>", normal_style))
                strong_points_text = sections["strong_points"]
                story.append(Paragraph(prepare_text_for_pdf(strong_points_text), get_paragraph_style(strong_points_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("legal_basis") and sections.get("legal_basis").strip():
                story.append(Paragraph("<b>d. Saudi Legal Basis</b>", normal_style))
                legal_basis_text = sections["legal_basis"]
                story.append(Paragraph(prepare_text_for_pdf(legal_basis_text), get_paragraph_style(legal_basis_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("risk_analysis") and sections.get("risk_analysis").strip():
                story.append(Paragraph("<b>e. Legal Risk Analysis</b>", normal_style))
                risk_text = sections["risk_analysis"]
                story.append(Paragraph(prepare_text_for_pdf(risk_text), get_paragraph_style(risk_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("obligations_rights") and sections.get("obligations_rights").strip():
                story.append(Paragraph("<b>f. Obligations and Rights</b>", normal_style))
                obligations_text = sections["obligations_rights"]
                story.append(Paragraph(prepare_text_for_pdf(obligations_text), get_paragraph_style(obligations_text)))
                story.append(Spacer(1, 0.05*inch))
            
            story.append(Spacer(1, 0.1*inch))
        
        # Recommendations
        if (sections.get("recommendations") or 
            sections.get("settlement_recommendations") or 
            sections.get("legal_action_recommendations") or 
            sections.get("protection_recommendations")):
            story.append(Paragraph("<b>3. Practical Recommendations</b>", heading_style))
            
            if sections.get("settlement_recommendations") and sections.get("settlement_recommendations").strip():
                story.append(Paragraph("<b>a. Settlement Recommendations</b>", normal_style))
                settlement_text = sections["settlement_recommendations"]
                story.append(Paragraph(prepare_text_for_pdf(settlement_text), get_paragraph_style(settlement_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("legal_action_recommendations") and sections.get("legal_action_recommendations").strip():
                story.append(Paragraph("<b>b. Legal Action Recommendations</b>", normal_style))
                legal_action_text = sections["legal_action_recommendations"]
                story.append(Paragraph(prepare_text_for_pdf(legal_action_text), get_paragraph_style(legal_action_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("protection_recommendations") and sections.get("protection_recommendations").strip():
                story.append(Paragraph("<b>c. Protection Recommendations</b>", normal_style))
                protection_text = sections["protection_recommendations"]
                story.append(Paragraph(prepare_text_for_pdf(protection_text), get_paragraph_style(protection_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("recommendations") and sections.get("recommendations").strip():
                recommendations_text = sections["recommendations"]
                story.append(Paragraph(prepare_text_for_pdf(recommendations_text), get_paragraph_style(recommendations_text)))
            
            story.append(Spacer(1, 0.1*inch))
        
        # Client Information
        if (sections.get("client_information") or 
            sections.get("simple_explanation") or 
            sections.get("next_steps")):
            story.append(Paragraph("<b>4. Information for Client/User</b>", heading_style))
            
            if sections.get("simple_explanation") and sections.get("simple_explanation").strip():
                story.append(Paragraph("<b>a. Simple Explanation</b>", normal_style))
                explanation_text = sections["simple_explanation"]
                story.append(Paragraph(prepare_text_for_pdf(explanation_text), get_paragraph_style(explanation_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("next_steps") and sections.get("next_steps").strip():
                story.append(Paragraph("<b>b. Next Steps</b>", normal_style))
                next_steps_text = sections["next_steps"]
                story.append(Paragraph(prepare_text_for_pdf(next_steps_text), get_paragraph_style(next_steps_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("client_information") and sections.get("client_information").strip():
                client_info_text = sections["client_information"]
                story.append(Paragraph(prepare_text_for_pdf(client_info_text), get_paragraph_style(client_info_text)))
            
            story.append(Spacer(1, 0.1*inch))
        
        # Advanced Analysis for Lawyers
        if (sections.get("legal_strategy") or 
            sections.get("legal_research") or 
            sections.get("professional_risks")):
            story.append(Paragraph("<b>5. Advanced Analysis for Lawyers</b>", heading_style))
            
            if sections.get("legal_strategy") and sections.get("legal_strategy").strip():
                story.append(Paragraph("<b>a. Legal Strategy</b>", normal_style))
                strategy_text = sections["legal_strategy"]
                story.append(Paragraph(prepare_text_for_pdf(strategy_text), get_paragraph_style(strategy_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("legal_research") and sections.get("legal_research").strip():
                story.append(Paragraph("<b>b. Required Legal Research</b>", normal_style))
                research_text = sections["legal_research"]
                story.append(Paragraph(prepare_text_for_pdf(research_text), get_paragraph_style(research_text)))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("professional_risks") and sections.get("professional_risks").strip():
                story.append(Paragraph("<b>c. Professional Risks</b>", normal_style))
                prof_risks_text = sections["professional_risks"]
                story.append(Paragraph(prepare_text_for_pdf(prof_risks_text), get_paragraph_style(prof_risks_text)))
                story.append(Spacer(1, 0.05*inch))
            
            story.append(Spacer(1, 0.1*inch))
        
        # Quantitative Assessment
        if sections.get("quantitative_assessment") and sections.get("quantitative_assessment").strip():
            story.append(Paragraph("<b>6. Quantitative Assessment</b>", heading_style))
            quantitative_text = sections["quantitative_assessment"]
            story.append(Paragraph(prepare_text_for_pdf(quantitative_text), get_paragraph_style(quantitative_text)))
            story.append(Spacer(1, 0.1*inch))
        
        # Legal References
        if sections.get("legal_references") and sections.get("legal_references").strip():
            story.append(Paragraph("<b>7. Legal References</b>", heading_style))
            references_text = sections["legal_references"]
            story.append(Paragraph(prepare_text_for_pdf(references_text), get_paragraph_style(references_text)))
            story.append(Spacer(1, 0.1*inch))
        
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Generate filename - use ASCII-safe filename for Content-Disposition
        safe_filename = "".join(c for c in analysis.filename if c.isalnum() or c in (' ', '-', '_')).strip()
        # Replace any remaining non-ASCII characters
        safe_filename = safe_filename.encode('ascii', 'ignore').decode('ascii')
        filename = f"analysis_{analysis_id}_{safe_filename}_{analysis.created_at.strftime('%Y%m%d')}.pdf"
        
        # Use RFC 5987 format for filename with UTF-8 encoding to support Arabic characters
        encoded_filename = quote(filename, safe='')
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    
    except HTTPException:
        raise
    except ImportError:
        logger.error("reportlab not installed. Cannot generate PDF.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "PDF generation not available. Please install reportlab.",
                "data": None,
                "errors": []
            }
        )
    except Exception as e:
        logger.exception("Error generating PDF")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Failed to generate PDF: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.delete("/analysis/{analysis_id}", response_model=None)
async def delete_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete an analysis from history."""
    try:
        # Get user's profile ID
        profile_service = ProfileService(db)
        profile = await profile_service.get_profile_response_by_id(current_user.sub)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Profile not found",
                    "data": None,
                    "errors": []
                }
            )
        
        history_service = CaseAnalysisHistoryService(db)
        deleted = await history_service.delete_analysis(analysis_id, profile.id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Analysis not found",
                    "data": None,
                    "errors": []
                }
            )
        
        return {
            "success": True,
            "message": "Analysis deleted successfully",
            "data": None,
            "errors": []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Failed to delete analysis: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


@router.post("/analyse-contract", response_model=None)
async def analyse_contract(
    file: UploadFile = File(..., description="Contract file (PDF, DOCX, DOC)"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Analyze a contract file using Gemini AI.
    Sends the file directly to Gemini and returns structured analysis with weak points, risks, and suggestions.
    """
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "No file provided",
                    "data": None,
                    "errors": [{"field": "file", "message": "No file provided"}]
                }
            )
        
        valid_extensions = ['pdf', 'docx', 'doc', 'txt']
        file_extension = file.filename.lower().split('.')[-1]
        
        if file_extension not in valid_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": f"Invalid file type: {file.filename}. Only PDF, DOCX, DOC, and TXT are supported.",
                    "data": None,
                    "errors": [{"field": "file", "message": f"Invalid file type: {file.filename}"}]
                }
            )
        
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        
        if file_size_mb > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": f"File {file.filename} is too large ({file_size_mb:.1f}MB). Maximum size is 20MB.",
                    "data": None,
                    "errors": [{"field": "file", "message": f"File {file.filename} exceeds size limit"}]
                }
            )
        
        contract_service = ContractAnalysisService()
        
        logger.info(f"Starting contract analysis for file: {file.filename}")
        
        result = await contract_service.analyze_contract(
            file_content=file_content,
            filename=file.filename
        )
        
        logger.info(f"Contract analysis result - success: {result.get('success')}, has data: {'data' in result}")
        
        if result.get("success") and result.get("data"):
            return {
                "success": True,
                "message": result.get("message", "Contract analysis completed successfully"),
                "data": result.get("data"),
                "errors": []
            }
        else:
            error_message = result.get("message", "Contract analysis failed")
            logger.error(f"Contract analysis failed: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": error_message,
                    "data": None,
                    "errors": [{"field": None, "message": error_message}]
                }
            )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.exception("Unexpected error during contract analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Failed to analyze contract: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
        )


