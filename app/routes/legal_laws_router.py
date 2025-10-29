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
import json
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query, HTTPException, Path, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal.knowledge.legal_laws_service import LegalLawsService
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..utils.auth import get_current_user
from ..models.user import User
from ..schemas.profile_schemas import TokenData

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
async def upload_legal_file(
    file: UploadFile = File(..., description="Legal document file (JSON, PDF, DOCX, TXT)"),
    law_name: Optional[str] = Form(None, description="Name of the law"),
    law_type: Optional[str] = Form(None, description="Type: law, regulation, code, directive, decree"),
    jurisdiction: Optional[str] = Form(None, description="Jurisdiction (e.g., المملكة العربية السعودية)"),
    issuing_authority: Optional[str] = Form(None, description="Issuing authority (e.g., وزارة العمل)"),
    issue_date: Optional[str] = Form(None, description="Issue date (YYYY-MM-DD format)"),
    last_update: Optional[str] = Form(None, description="Last update date (YYYY-MM-DD)"),
    description: Optional[str] = Form(None, description="Law description"),
    source_url: Optional[str] = Form(None, description="Source URL"),
    use_ai: bool = Query(True, description="Use AI extractor when available"),
    fallback_on_failure: bool = Query(True, description="Fallback to local parser if AI fails"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🎯 Unified Upload Endpoint - Smart Legal Document Processor
    
    Automatically detects and handles different file types:
    - **JSON**: Extracts law sources and articles directly from structured JSON
    - **PDF/DOCX/TXT**: Saves file and prepares for AI or manual parsing
    - **Status Management**: Automatically updates law status (unhandled → processing → processed)
    
    **Supported File Types:**
    - `.json` - Structured legal documents with law sources and articles
    - `.pdf` - Legal documents (requires AI parsing)
    - `.docx`, `.doc` - Word documents (requires AI parsing)
    - `.txt` - Plain text documents
    
    **Processing Workflow:**
    1. File upload → Status: `raw` (unhandled)
    2. File validation → SHA-256 duplicate detection
    3. File type detection → Route to appropriate handler
    4. Document creation → Store metadata
    5. Law source creation → Link to document
    6. For JSON: Extract articles immediately → Status: `processed`
    7. For others: Status remains `raw` until parsing
    
    **JSON Structure Example:**
    ```json
    {
        "law_sources": [{
            "name": "نظام العمل",
            "type": "law",
            "jurisdiction": "المملكة العربية السعودية",
            "articles": [{
                "article": "1",
                "title": "Article Title",
                "text": "Article content...",
                "keywords": ["keyword1", "keyword2"]
            }]
        }]
    }
    ```
    
    **Returns:**
    - Document metadata and processing status
    - Count of created law sources, articles, and chunks
    - Processing time and file size information
    - Duplicate detection status
    """
    file_path = None
    try:
        # Step 1: Validate file
        if not file.filename:
            return create_error_response(
                message="No file provided",
                errors=[{"field": "file", "message": "File is required"}]
            )
        
        # Step 2: Detect file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = ['.json', '.pdf', '.docx', '.doc', '.txt']
        
        if file_extension not in allowed_extensions:
            return create_error_response(
                message="Unsupported file type",
                errors=[{
                    "field": "file",
                    "message": f"File type '{file_extension}' not supported. Allowed: {', '.join(allowed_extensions)}"
                }]
            )
        
        logger.info(f"📄 Detected file type: {file_extension} for {file.filename}")
        
        # Step 3: Validate law_type if provided
        if law_type:
            valid_types = ['law', 'regulation', 'code', 'directive', 'decree']
            if law_type not in valid_types:
                return create_error_response(
                    message=f"Invalid law_type. Must be one of: {', '.join(valid_types)}"
                )
        
        # Step 4: Create upload directory
        upload_dir = "uploads/legal_documents"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Step 5: Save file with unique name
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"💾 Saved file: {file_path}")
        
        # Step 6: Calculate file hash for duplicate detection
        file_hash = calculate_file_hash(file_path)
        logger.info(f"🔐 File hash: {file_hash[:16]}...")
        
        # Step 7: Parse dates if provided
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
        
        # Step 8: Route to appropriate handler based on file type
        service = LegalLawsService(db)
        
        if file_extension == '.json':
            # Handle JSON files
            logger.info("🔧 Processing JSON file")
            
            # Read JSON content
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Extract title from JSON if not provided
            json_title = "Law Document"
            if "law_sources" in json_data:
                law_sources = json_data["law_sources"]
                if isinstance(law_sources, dict):
                    json_title = law_sources.get("name", "Law Document")
                    law_type = law_type or law_sources.get("type", "law")
                elif isinstance(law_sources, list) and len(law_sources) > 0:
                    json_title = law_sources[0].get("name", "Law Document")
                    law_type = law_type or law_sources[0].get("type", "law")
            
            # Process JSON using upload_json_law_structure
            result = await service.upload_json_law_structure(
                json_data=json_data,
                uploaded_by=current_user.sub if current_user else 1
            )
            
            if result["success"]:
                return create_success_response(
                    message=f"✅ Successfully processed JSON law: {result['message']}",
                    data=result["data"]
                )
            else:
                # Clean up file on failure
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Return error with proper HTTP status code
                from fastapi.responses import JSONResponse
                error_response = create_error_response(
                    message=result["message"],
                    errors=result.get("errors", [])
                )
                return JSONResponse(
                    status_code=400,
                    content=error_response.model_dump()
                )
        
        else:
            # Handle PDF, DOCX, TXT files
            logger.info(f"🔧 Processing {file_extension.upper()} file")
            
            # Validate required metadata for non-JSON files
            if not law_name:
                return create_error_response(
                    message="law_name is required for non-JSON files",
                    errors=[{"field": "law_name", "message": "Law name is required"}]
                )
            
            if not law_type:
                law_type = "law"  # Default
            
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
            
            # Process using upload_and_parse_law
            result = await service.upload_and_parse_law(
                file_path=file_path,
                file_hash=file_hash,
                original_filename=file.filename,
                law_source_details=law_source_details,
                uploaded_by=current_user.sub if current_user else 1,
                use_ai=use_ai,
                fallback_on_failure=fallback_on_failure
            )
            
            if result["success"]:
                return create_success_response(
                    message=result["message"],
                    data=result["data"]
                )
            else:
                # Clean up file on failure
                if os.path.exists(file_path):
                    os.remove(file_path)
                return create_error_response(
                    message=result["message"],
                    errors=result.get("errors", [])
                )
    
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        
        # Clean up file on validation error
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        return create_error_response(
            message="Document validation failed",
            errors=[{"field": "file", "message": str(e)}]
        )
    
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing error: {e}")
        
        # Clean up file on JSON error
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        return create_error_response(
            message="Invalid JSON format",
            errors=[{"field": "file", "message": f"Invalid JSON: {str(e)}"}]
        )
    
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}", exc_info=True)
        
        # Clean up file on error
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        return create_error_response(
            message=f"Failed to upload document: {str(e)}"
        )


# ===========================================
# DEPRECATED ENDPOINTS (Keeping for backwards compatibility)
# Use the unified /upload endpoint instead
# ===========================================

@router.post("/upload-legacy-pdf", deprecated=True, response_model=ApiResponse)
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
    use_ai: bool = Query(True, description="Use Gemini AI extractor"),
    fallback_on_failure: bool = Query(True, description="Fallback to local parser if AI fails"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ⚠️ DEPRECATED: Use /upload instead. This endpoint will be removed in a future version.
    
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
            uploaded_by=current_user.sub,
            use_ai=use_ai,
            fallback_on_failure=fallback_on_failure
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


@router.post("/upload-gemini-only", deprecated=True, response_model=ApiResponse)
async def upload_and_parse_law_gemini_only(
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
    ⚠️ DEPRECATED: Use /upload with use_ai=True and fallback_on_failure=False.
    This endpoint will be removed in a future version.
    
    Upload and parse a legal law PDF using ONLY Gemini AI extractor.
    
    **Key Differences from /upload:**
    - Uses ONLY Gemini AI for extraction (no local parser fallback)
    - Fails immediately if Gemini AI is unavailable or fails
    - Ensures consistent AI-powered extraction quality
    - No fallback mechanisms - pure AI processing
    
    **Workflow:**
    1. Save PDF and calculate SHA-256 hash
    2. Create KnowledgeDocument with file hash (prevents duplicates)
    3. Create LawSource linked to KnowledgeDocument
    4. Parse PDF using ONLY Gemini AI to extract hierarchy: Branches → Chapters → Articles
    5. Create KnowledgeChunks for each article
    6. Update status to 'processed'
    7. Return full hierarchical tree
    
    **Returns:**
    Complete law structure with branches, chapters, and articles.
    
    **Error Handling:**
    - Returns error if Gemini AI fails (no fallback)
    - Returns error if AI service is unavailable
    - Ensures consistent AI-powered results
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
        
        # Process the document using ONLY Gemini AI (no fallback)
        service = LegalLawsService(db)
        result = await service.upload_and_parse_law(
            file_path=file_path,
            file_hash=file_hash,
            original_filename=pdf_file.filename,
            law_source_details=law_source_details,
            uploaded_by=current_user.sub,
            use_ai=True,  # Force AI usage
            fallback_on_failure=False  # Disable fallback - Gemini only
        )
        
        if result["success"]:
            return create_success_response(
                message=f"✅ Successfully processed using Gemini AI only: {result['message']}",
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
                message=f"❌ Gemini AI processing failed: {result['message']}",
                errors=result.get("errors", [])
            )
            
    except Exception as e:
        logger.error(f"Failed to upload and parse law with Gemini only: {str(e)}")
        
        # Clean up file on error
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        
        return create_error_response(
            message=f"Failed to upload and parse law with Gemini only: {str(e)}"
        )


@router.post("/upload-document", deprecated=True, response_model=ApiResponse)
async def upload_legal_document(
    file: UploadFile = File(..., description="Legal document file (JSON, PDF, DOCX, TXT)"),
    title: str = Form(..., description="Document title"),
    category: str = Form(..., description="Document category: law, article, manual, policy, contract"),
    uploaded_by: Optional[int] = Form(None, description="User ID who uploaded the document"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """
    ⚠️ DEPRECATED: Use /upload instead. This endpoint will be removed in a future version.
    
    Upload a legal document for processing and knowledge extraction with dual database support.
    
    **Supported File Types:**
    - JSON: Structured legal documents with law sources and articles
    - PDF: Legal documents (placeholder for future implementation)
    - DOCX: Word documents (placeholder for future implementation)
    - TXT: Plain text documents (placeholder for future implementation)
    
    **JSON Document Structure:**
    ```json
    {
        "law_sources": [
            {
                "name": "Law Name",
                "type": "law",
                "jurisdiction": "Saudi Arabia",
                "issuing_authority": "Ministry",
                "issue_date": "2023-01-01",
                "last_update": "2023-12-01",
                "description": "Description",
                "source_url": "URL",
                "articles": [
                    {
                        "article": "1",
                        "title": "Article Title",
                        "text": "Article content...",
                        "keywords": ["keyword1", "keyword2"],
                        "order_index": 1
                    }
                ]
            }
        ]
    }
    ```
    
    **Processing Features:**
    - Automatic duplicate detection using SHA-256 hash
    - Hierarchical content parsing (Law Sources → Articles → Chunks)
    - Bulk database operations for optimal performance
    - Comprehensive error handling and logging
    - Real-time processing statistics
    - Dual database support (SQL + Chroma)
    
    **Response Includes:**
    - Document metadata and processing status
    - Count of created law sources, articles, and chunks
    - Detailed summaries of all created entities
    - Processing time and file size information
    - Duplicate detection status
    
    **Error Handling:**
    - File validation (type, size, format)
    - JSON structure validation
    - Database constraint violations
    - Processing failures with detailed error messages
    """
    logger.info(f"🚀 Starting document upload: {file.filename}")
    
    try:
        # Validate file
        if not file.filename:
            return create_error_response(
                message="No file provided",
                errors=[{"field": "file", "message": "File is required"}]
            )
        
        # Validate file type
        allowed_extensions = ['.json', '.pdf', '.docx', '.doc', '.txt']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            return create_error_response(
                message="Unsupported file type",
                errors=[{
                    "field": "file", 
                    "message": f"File type '{file_extension}' not supported. Allowed types: {', '.join(allowed_extensions)}"
                }]
            )
        
        # Validate category
        allowed_categories = ['law', 'article', 'manual', 'policy', 'contract']
        if category not in allowed_categories:
            return create_error_response(
                message="Invalid category",
                errors=[{
                    "field": "category",
                    "message": f"Category must be one of: {', '.join(allowed_categories)}"
                }]
            )
        
        # Validate title
        if not title or len(title.strip()) < 1:
            return create_error_response(
                message="Invalid title",
                errors=[{"field": "title", "message": "Title is required and cannot be empty"}]
            )
        
        # Use current user ID if not provided
        user_id = uploaded_by or (current_user.sub if current_user else None)
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            return create_error_response(
                message="Empty file",
                errors=[{"field": "file", "message": "File is empty"}]
            )
        
        # Check file size (limit to 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_content) > max_size:
            return create_error_response(
                message="File too large",
                errors=[{
                    "field": "file",
                    "message": f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({max_size} bytes)"
                }]
            )
        
        logger.info(f"📁 File validation passed: {file.filename} ({len(file_content)} bytes)")
        
        # Initialize upload service
        service = LegalLawsService(db)
        
        # Process JSON upload using LegalLawsService
        result = await service.upload_json_law_structure(
            json_data=json.loads(file_content.decode('utf-8')),
            uploaded_by=user_id or current_user.sub
        )
        
        # Convert result to response format
        response_data = result.get("data", {})
        
        logger.info(f"✅ Document upload completed successfully")
        
        return create_success_response(
            message=f"Document '{title}' uploaded and processed successfully",
            data=response_data
        )
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        return create_error_response(
            message="Document validation failed",
            errors=[{"field": "file", "message": str(e)}]
        )
    
    except NotImplementedError as e:
        logger.error(f"❌ Feature not implemented: {e}")
        return create_error_response(
            message="File type processing not yet implemented",
            errors=[{"field": "file", "message": str(e)}]
        )
    
    except Exception as e:
        logger.error(f"❌ Document upload failed: {e}")
        return create_error_response(
            message=f"Failed to upload document: {str(e)}"
        )


@router.post("/upload-json", deprecated=True, response_model=ApiResponse)
async def upload_law_json(
    file: UploadFile = File(..., description="JSON file containing law structure with articles"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> ApiResponse:
    """
    ⚠️ DEPRECATED: Use /upload instead. This endpoint will be removed in a future version.
    
    Upload a legal law JSON document for processing with dual database support (SQL + Chroma).
    
    **Supported JSON Structure:**
    ```json
    {
        "law_sources": [
            {
                    "name": "نظام العمل",
                    "type": "law",
                    "jurisdiction": "المملكة العربية السعودية",
                    "issuing_authority": "ملك المملكة العربية السعودية (مرسوم ملكي رقم م/11 بتاريخ 18 / 2 / 1435)",
                    "issue_date": "1435/02/18هـ",
                    "description": "نظام جزائي يهدف إلى مكافحة جرائم التزوير بمختلف صورها المتعلقة بالأختام والعلامات والطوابع والمحررات، ويحدد العقوبات المقررة لكل جريمة والأحكام العامة المتعلقة بالشروع والاشتراك والانقضاء.",
                    "status": "processed",
                "articles": [
                    {
                        "article": "1 المادة ",
                        "text": "Article Title",
                       
                    }
                ]
            }
        ]
    }
    ```
    
    **Processing Features:**
    - Automatic duplicate detection using SHA-256 hash
    - Hierarchical content parsing (Law Sources → Articles → Chunks)
    - Dual database support (SQL + Chroma)
    - Bulk database operations for optimal performance
    - Comprehensive error handling with rollback
    - Real-time processing statistics
    
    **Response Includes:**
    - Document metadata and processing status
    - Count of created law sources, articles, and chunks
    - Detailed summaries of all created entities
    - Processing time and file size information
    - Duplicate detection status
    """
    logger.info(f"🚀 Starting JSON law upload: {file.filename}")
    
    try:
        # Validate file
        if not file.filename:
            return create_error_response(
                message="No file provided",
                errors=[{"field": "file", "message": "File is required"}]
            )
        
        # Validate file type
        if not file.filename.lower().endswith('.json'):
            from fastapi.responses import JSONResponse
            error_response = create_error_response(
                message="Invalid file type",
                errors=[{
                    "field": "file", 
                    "message": "Only JSON files are supported"
                }]
            )
            return JSONResponse(status_code=400, content=error_response.model_dump())
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            from fastapi.responses import JSONResponse
            error_response = create_error_response(
                message="Empty file",
                errors=[{"field": "file", "message": "File is empty"}]
            )
            return JSONResponse(status_code=400, content=error_response.model_dump())
        
        # Check file size (limit to 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_content) > max_size:
            from fastapi.responses import JSONResponse
            error_response = create_error_response(
                message="File too large",
                errors=[{
                    "field": "file",
                    "message": f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({max_size} bytes)"
                }]
            )
            return JSONResponse(status_code=400, content=error_response.model_dump())
        
        # Parse JSON to get title
        try:
            json_data = json.loads(file_content.decode('utf-8'))
            # Extract law name as title - handle both dict and list formats
            if "law_sources" in json_data:
                law_sources = json_data["law_sources"]
                # Handle both dict (single law source) and list (multiple law sources)
                if isinstance(law_sources, dict):
                    title = law_sources.get("name", "Law Document")
                    category = law_sources.get("type", "law")
                elif isinstance(law_sources, list) and len(law_sources) > 0:
                    title = law_sources[0].get("name", "Law Document")
                    category = law_sources[0].get("type", "law")
                else:
                    title = "Law Document"
                    category = "law"
            else:
                title = "Law Document"
                category = "law"
        except json.JSONDecodeError as e:
            from fastapi.responses import JSONResponse
            error_response = create_error_response(
                message="Invalid JSON format",
                errors=[{"field": "file", "message": f"Invalid JSON: {str(e)}"}]
            )
            return JSONResponse(status_code=400, content=error_response.model_dump())
        
        logger.info(f"📁 File validation passed: {file.filename} ({len(file_content)} bytes)")
        
        # Debug logging
        logger.info(f"🔍 Current user: {current_user}")
        logger.info(f"🔍 User sub (ID): {current_user.sub}")
        logger.info(f"🔍 User email: {current_user.email if hasattr(current_user, 'email') else 'N/A'}")
        
        # Initialize upload service
        service = LegalLawsService(db)
        
        # Process JSON upload using LegalLawsService
        user_id = current_user.sub if hasattr(current_user, 'sub') else 1
        logger.info(f"🔍 Using user_id: {user_id}")
        
        result = await service.upload_json_law_structure(
            json_data=json_data,
            uploaded_by=user_id
        )
        
        # Convert result to response format
        if result.get("success"):
            response_data = result.get("data", {})
        else:
            # Return error response with 400 status code
            from fastapi.responses import JSONResponse
            error_response = create_error_response(
                message=result.get("message", "Failed to upload JSON law"),
                errors=result.get("errors", [])
            )
            return JSONResponse(
                status_code=400,
                content=error_response.model_dump()
            )
        
        logger.info(f"✅ JSON law upload completed successfully")
        
        return create_success_response(
            message=f"JSON law document '{title}' uploaded and processed successfully",
            data=response_data
        )
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        from fastapi.responses import JSONResponse
        error_response = create_error_response(
            message="JSON validation failed",
            errors=[{"field": "file", "message": str(e)}]
        )
        return JSONResponse(status_code=400, content=error_response.model_dump())
    
    except NotImplementedError as e:
        logger.error(f"❌ Feature not implemented: {e}")
        from fastapi.responses import JSONResponse
        error_response = create_error_response(
            message="File type processing not yet implemented",
            errors=[{"field": "file", "message": str(e)}]
        )
        return JSONResponse(status_code=501, content=error_response.model_dump())
    
    except Exception as e:
        logger.error(f"❌ JSON law upload failed: {e}", exc_info=True)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        from fastapi.responses import JSONResponse
        error_response = create_error_response(
            message=f"Failed to upload JSON law: {str(e)}"
        )
        return JSONResponse(status_code=500, content=error_response.model_dump())


# ===========================================
# CHROMA EMBEDDINGS AND QUERY
# ===========================================

@router.post("/{law_id}/generate-embeddings", response_model=ApiResponse)
async def generate_embeddings_for_document(
    law_id: int = Path(..., gt=0, description="Law Source ID to generate embeddings for"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Generate Chroma embeddings for all chunks of a specific document (runs in background).
    
    **What it does:**
    - Retrieves all chunks from SQL database for the specified document
    - Creates embeddings for each chunk using the embedding model
    - Stores embeddings in Chroma vectorstore for similarity search
    - Returns statistics about the operation
    
    **Important:** This operation runs in the background to prevent server timeouts.
    
    **Use this when:**
    - You've uploaded a document and want to make it searchable
    - You want to regenerate embeddings for an existing document
    - The document has chunks in SQL but no embeddings in Chroma
    
    **Returns:**
    - Success status (operation started in background)
    - Document ID
    - Processing message
    """
    try:
        from sqlalchemy import select
        from ..models import LawSource
        from ..services.legal.knowledge.document_parser_service import DocumentUploadService
        
        # Step 1: Get the law source to find the document ID
        law_result = await db.execute(
            select(LawSource).where(LawSource.id == law_id)
        )
        law = law_result.scalar_one_or_none()
        
        if not law:
            return create_error_response(
                message=f"Law with ID {law_id} not found"
            )
        
        if not law.knowledge_document_id:
            return create_error_response(
                message=f"Law {law_id} has no associated document"
            )
        
        document_id = law.knowledge_document_id
        logger.info(f"📋 Law {law_id} -> Document {document_id} for embedding generation")
        
        # Step 2: Initialize the service
        service = DocumentUploadService(db)
        
        # Step 3: Run embedding generation in background (async task)
        async def run_embeddings():
            try:
                await service.generate_embeddings_for_document(document_id)
            except Exception as e:
                logger.error(f"❌ Background embedding generation failed for law {law_id}: {e}", exc_info=True)
        
        import asyncio
        asyncio.create_task(run_embeddings())
        
        logger.info(f"🚀 Started background embedding generation for law {law_id} (document {document_id})")
        
        return create_success_response(
            message=f"Embedding generation started in background for law '{law.name}'",
            data={
                "law_id": law_id,
                "law_name": law.name,
                "document_id": document_id,
                "status": "processing",
                "message": "Embeddings are being generated in the background. Check logs for progress."
            }
        )
            
    except Exception as e:
        logger.error(f"❌ Failed to start embedding generation: {e}", exc_info=True)
        from fastapi.responses import JSONResponse
        error_response = create_error_response(
            message=f"Failed to start embedding generation: {str(e)}"
        )
        return JSONResponse(status_code=500, content=error_response.model_dump())


@router.post("/query", response_model=ApiResponse)
async def answer_query(
    query: str = Query(..., description="Search query or question"),
    document_id: Optional[int] = Query(None, description="Optional document ID to filter results"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to retrieve (1-20)"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Answer a query using Chroma similarity search and Gemini AI.
    
    **How it works:**
    - Searches the Chroma vectorstore for chunks similar to your query
    - Uses Gemini AI to generate a clear, contextualized answer
    - Returns a professional legal answer in Arabic
    
    **Features:**
    - Semantic search across all uploaded legal documents
    - AI-generated answers based on relevant articles
    - Cites specific article numbers and law sources
    - Optional filtering by document ID
    
    **Returns:**
    - `answer`: A clear, AI-generated answer to your question
    - `query`: The original question
    - `message`: Status message
    
    **Example Query:**
    "ماهي مهام واختصاصات مفتشي العمل؟"
    
    **Example Response:**
    ```json
    {
      "success": true,
      "message": "Found 5 relevant results",
      "data": {
        "answer": "بناءً على المادة 138 من نظام العمل السعودي...",
        "query": "ماهي مهام واختصاصات مفتشي العمل؟"
      }
    }
    ```
    """
    try:
        from ..services.legal.knowledge.document_parser_service import DocumentUploadService
        
        # Initialize the service
        service = DocumentUploadService(db)
        
        # Perform the query (now returns AI-generated answer)
        result = await service.answer_query(
            query=query,
            document_id=document_id,
            top_k=top_k
        )
        
        if result.get("success"):
            # Return only the answer and query (no raw chunks)
            return create_success_response(
                message=result.get("answer", "تم معالجة السؤال بنجاح"),
                data={
                    "answer": result.get("answer", ""),
                    "query": result.get("query", query)
                }
            )
        else:
            from fastapi.responses import JSONResponse
            error_response = create_error_response(
                message=result.get("answer", result.get("message", "فشل في معالجة السؤال"))
            )
            return JSONResponse(
                status_code=400,
                content=error_response.model_dump()
            )
            
    except Exception as e:
        logger.error(f"❌ Query failed: {e}", exc_info=True)
        from fastapi.responses import JSONResponse
        error_response = create_error_response(
            message="حدث خطأ أثناء معالجة السؤال. يرجى المحاولة مرة أخرى."
        )
        return JSONResponse(status_code=500, content=error_response.model_dump())


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


@router.get("/{law_id}/articles", response_model=ApiResponse)
async def get_law_articles(
    law_id: int = Path(..., gt=0, description="Law source ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all articles of a specific law.
    
    **Returns:**
    Law metadata with all articles containing:
    - Article ID, number, title, and content
    - Keywords (if available)
    - Order index for sorting
    - AI processing status
    - Creation timestamps
    
    **Note:** Articles are sorted by their order_index.
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
        logger.error(f"Failed to get law articles: {str(e)}")
        return create_error_response(message=f"Failed to get law articles: {str(e)}")


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
