"""
Legal Document Upload API Router

This router provides endpoints for uploading and processing legal documents
in various formats (JSON, PDF, DOCX, TXT) with comprehensive metadata handling.
"""

import logging
import os
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.document_parser_service import DocumentUploadService
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..schemas.document_upload import DocumentUploadResponse
from ..utils.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["Document Upload"])


@router.post("/upload", response_model=ApiResponse[DocumentUploadResponse])
async def upload_legal_document(
    file: UploadFile = File(..., description="Legal document file (JSON, PDF, DOCX, TXT)"),
    title: str = Form(..., description="Document title"),
    category: str = Form(..., description="Document category: law, article, manual, policy, contract"),
    uploaded_by: Optional[int] = Form(None, description="User ID who uploaded the document"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[DocumentUploadResponse]:
    """
    Upload a legal document for processing and knowledge extraction.
    
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
        user_id = uploaded_by or (current_user.id if current_user else None)
        
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
        upload_service = DocumentUploadService(db)
        
        # Process document upload
        result = await upload_service.upload_document(
            file_content=file_content,
            filename=file.filename,
            title=title.strip(),
            category=category,
            uploaded_by=user_id
        )
        
        # Convert result to response model
        response_data = DocumentUploadResponse(**result)
        
        logger.info(f"✅ Document upload completed successfully: {response_data.document_id}")
        
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

