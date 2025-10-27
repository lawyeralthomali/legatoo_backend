
class LawSource(Base):
    """المصادر القانونية مثل القوانين واللوائح والأنظمة."""
    
    __tablename__ = "law_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, index=True)
    type = Column(String(50), CheckConstraint("type IN ('law', 'regulation', 'code', 'directive', 'decree')"))
    jurisdiction = Column(String(100), index=True)
    issuing_authority = Column(String(200))
    issue_date = Column(Date)
    last_update = Column(Date)
    description = Column(Text)
    source_url = Column(Text)
    knowledge_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), CheckConstraint("status IN ('raw', 'processed', 'indexed')"), default="raw", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    knowledge_document = relationship("KnowledgeDocument", foreign_keys=[knowledge_document_id])
    articles = relationship("LawArticle", back_populates="law_source", cascade="all, delete-orphan")
    chunks = relationship("KnowledgeChunk", back_populates="law_source")
    
    def __repr__(self):
        return f"<LawSource(id={self.id}, name='{self.name}', type='{self.type}')>"


# ---------------------------------------
# Law Articles
# ---------------------------------------
class LawArticle(Base):

    
    __tablename__ = "law_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    law_source_id = Column(Integer, ForeignKey("law_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    article_number = Column(String(50), index=True)
    title = Column(Text)
    content = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=True)  # Store keywords as JSON array
    order_index = Column(Integer, default=0)  # ترتيب المواد داخل المصدر القانوني
    source_document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    ai_processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    law_source = relationship("LawSource", back_populates="articles")
    source_document = relationship("KnowledgeDocument", foreign_keys=[source_document_id])
    chunks = relationship("KnowledgeChunk", back_populates="article")
    
    def __repr__(self):
        return f"<LawArticle(id={self.id}, article_number='{self.article_number}', law_source_id={self.law_source_id})>"






# Knowledge Documents
# ---------------------------------------
class KnowledgeDocument(Base):
    """Documents uploaded for knowledge ingestion."""
    
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    category = Column(String(50), CheckConstraint("category IN ('law', 'case', 'contract', 'article', 'policy', 'manual')"))
    file_path = Column(Text)
    file_extension = Column(String(20), nullable=True)  # Store file extension (.json, .pdf, .docx, etc.)
    file_hash = Column(String(64), unique=True, index=True, nullable=True)
    source_type = Column(String(50), CheckConstraint("source_type IN ('uploaded', 'web_scraped', 'api_import')"))
    status = Column(String(50), CheckConstraint("status IN ('raw', 'processed', 'indexed', 'pending_parsing')"), default="raw")
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True))
    document_metadata = Column(JSON)
    
    # Relationships
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, title='{self.title}', category='{self.category}')>"



legal_laws_router.py:


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
    use_ai: bool = Query(True, description="Use Gemini AI extractor"),
    fallback_on_failure: bool = Query(True, description="Fallback to local parser if AI fails"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
   
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


@router.post("/upload-gemini-only", response_model=ApiResponse)
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


@router.post("/upload-document", response_model=ApiResponse)
async def upload_legal_document(
    file: UploadFile = File(..., description="Legal document file (JSON, PDF, DOCX, TXT)"),
    title: str = Form(..., description="Document title"),
    category: str = Form(..., description="Document category: law, article, manual, policy, contract"),
    uploaded_by: Optional[int] = Form(None, description="User ID who uploaded the document"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse:
    """
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


@router.post("/upload-json", response_model=ApiResponse)
async def upload_law_json(
    file: UploadFile = File(..., description="JSON file containing law structure with articles"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
) -> ApiResponse:
    """
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

@router.post("/{document_id}/generate-embeddings", response_model=ApiResponse)
async def generate_embeddings_for_document(
    document_id: int = Path(..., gt=0, description="Document ID to generate embeddings for"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    try:
        from ..services.legal.knowledge.document_parser_service import DocumentUploadService
        
        # Initialize the service
        service = DocumentUploadService(db)
        
        # Run embedding generation in background to prevent server hang
        background_tasks.add_task(service.generate_embeddings_for_document, document_id)
        
        logger.info(f"🚀 Started background embedding generation for document {document_id}")
        
        return create_success_response(
            message=f"Embedding generation started in background for document {document_id}",
            data={
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
    top_k: int = Query(5, ge=1, le=20, description="Number of results to return (1-20)"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
 
    try:
        from ..services.legal.knowledge.document_parser_service import DocumentUploadService
        
        # Initialize the service
        service = DocumentUploadService(db)
        
        # Perform the query
        result = await service.answer_query(
            query=query,
            document_id=document_id,
            top_k=top_k
        )
        
        if result.get("success"):
            return create_success_response(
                message=result.get("message", "Query completed successfully"),
                data=result
            )
        else:
            from fastapi.responses import JSONResponse
            error_response = create_error_response(
                message=result.get("message", "Query failed")
            )
            return JSONResponse(
                status_code=400,
                content=error_response.model_dump()
            )
            
    except Exception as e:
        logger.error(f"❌ Query failed: {e}", exc_info=True)
        from fastapi.responses import JSONResponse
        error_response = create_error_response(
            message=f"Query failed: {str(e)}"
        )
        return JSONResponse(status_code=500, content=error_response.model_dump())



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







now i want to merge the three uploaded file method  to only one and it must be handle the file according to its extended @legal_laws_router.py are you understand me for example upload_and_parse_law ,upload_and_parse_law_gemini_only ,upload_legal_document ,upload_law_json  
now if the file is a json it must handle with same logic in upload_law_json  and if it pdf it must extracted either by ai or using the current liberary in the  code and then saved to articles in table and it must set the status of the law  to  unhandled and if user generate the embedding of the law it must be change the status but i want to do something 
يعني بالمختصر ابغى يكون عندي حالا توضحة بحيث لما المستخدم يرفع الملف تكون له حاله ولما المستخدم يبدا عملية الembeding تصبح الحاله جاري المعالجة وعندما تكتمل المعالجة ونشاء embeding تصبح الحاله تمت المعالجة هذا ماقصده فقط ولذالك الان اريدك ان تقوم بانشاء برومت خطير جدا ودقيق لكي يقوم كاسر ai بالتعديل المطلوب بدقة وارجو ان تكون دقيق حتى انت واذا مو عارف اسماء الاشيا اعطه شرح عام ويكون فاهم له لا اريد ان ينشى اي اشياء فقط حاليا نريد التعديل 
