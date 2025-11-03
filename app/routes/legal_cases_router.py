"""
Legal Cases Router

API endpoints for ingesting and managing historical legal cases.
Follows clean architecture with thin routes delegating to service layer.
"""

import logging
import json
from typing import Optional, List
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
        
        # Create PDF document
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        
        # Define custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='#1f2937',
            spaceAfter=12,
            alignment=TA_LEFT
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='#374151',
            spaceAfter=8,
            spaceBefore=12,
            alignment=TA_LEFT
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor='#4b5563',
            spaceAfter=6,
            alignment=TA_LEFT,
            leading=14
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph(f"<b>Legal Case Analysis Report</b>", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # File Information
        story.append(Paragraph(f"<b>File:</b> {analysis.filename}", normal_style))
        story.append(Paragraph(f"<b>Analysis Type:</b> {analysis.analysis_type}", normal_style))
        story.append(Paragraph(f"<b>Lawsuit Type:</b> {analysis.lawsuit_type}", normal_style))
        story.append(Paragraph(f"<b>Date:</b> {analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
        if analysis.risk_score is not None:
            story.append(Paragraph(f"<b>Risk Score:</b> {analysis.risk_score}% ({analysis.risk_label})", normal_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Get analysis data
        analysis_data = analysis.analysis_data
        sections = analysis_data.get("analysis", {}).get("sections", {})
        
        # Helper function to safely escape HTML
        def escape_html(text):
            if not text:
                return ""
            return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Executive Summary
        if sections.get("executive_summary"):
            story.append(Paragraph("<b>1. Executive Summary</b>", heading_style))
            story.append(Paragraph(escape_html(sections["executive_summary"]), normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Legal Analysis sections
        if sections.get("legal_analysis") or sections.get("legal_status"):
            story.append(Paragraph("<b>2. Detailed Legal Analysis</b>", heading_style))
            
            if sections.get("legal_status"):
                story.append(Paragraph("<b>a. Current Legal Status</b>", normal_style))
                story.append(Paragraph(escape_html(sections["legal_status"]), normal_style))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("weak_points"):
                story.append(Paragraph("<b>b. Weak Points in the Case</b>", normal_style))
                story.append(Paragraph(escape_html(sections["weak_points"]), normal_style))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("strong_points"):
                story.append(Paragraph("<b>c. Strong Points in the Case</b>", normal_style))
                story.append(Paragraph(escape_html(sections["strong_points"]), normal_style))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("legal_basis"):
                story.append(Paragraph("<b>d. Saudi Legal Basis</b>", normal_style))
                story.append(Paragraph(escape_html(sections["legal_basis"]), normal_style))
                story.append(Spacer(1, 0.05*inch))
            
            if sections.get("risk_analysis"):
                story.append(Paragraph("<b>e. Legal Risk Analysis</b>", normal_style))
                story.append(Paragraph(escape_html(sections["risk_analysis"]), normal_style))
                story.append(Spacer(1, 0.05*inch))
            
            story.append(Spacer(1, 0.1*inch))
        
        # Recommendations
        if sections.get("recommendations"):
            story.append(Paragraph("<b>3. Practical Recommendations</b>", heading_style))
            story.append(Paragraph(escape_html(sections["recommendations"]), normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Client Information
        if sections.get("client_information") or sections.get("next_steps"):
            story.append(Paragraph("<b>4. Information for Client/User</b>", heading_style))
            if sections.get("client_information"):
                story.append(Paragraph(escape_html(sections["client_information"]), normal_style))
            if sections.get("next_steps"):
                story.append(Paragraph("<b>Next Steps:</b>", normal_style))
                story.append(Paragraph(escape_html(sections["next_steps"]), normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Legal References
        if sections.get("legal_references"):
            story.append(Paragraph("<b>Legal References</b>", heading_style))
            story.append(Paragraph(escape_html(sections["legal_references"]), normal_style))
            story.append(Spacer(1, 0.1*inch))
        
        # Full Analysis (fallback)
        if analysis.raw_response and not sections.get("executive_summary"):
            story.append(Paragraph("<b>Complete Analysis</b>", heading_style))
            full_text = escape_html(analysis.raw_response[:5000])  # Limit to avoid huge PDFs
            story.append(Paragraph(full_text, normal_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Generate filename
        safe_filename = "".join(c for c in analysis.filename if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"analysis_{analysis_id}_{safe_filename}_{analysis.created_at.strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
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


