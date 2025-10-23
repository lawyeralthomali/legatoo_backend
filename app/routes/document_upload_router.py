"""
Legal Document Upload API Router

This router provides endpoints for uploading and processing legal documents
in various formats (JSON, PDF, DOCX, TXT) with comprehensive metadata handling.
"""

import logging
import os
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.document_parser_service import DocumentUploadService
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..schemas.document_upload import DocumentUploadRequest, DocumentUploadResponse
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


@router.get("/upload/status/{document_id}", response_model=ApiResponse[Dict[str, Any]])
async def get_upload_status(
    document_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Get the processing status of an uploaded document.
    
    **Response Fields:**
    - document_id: The document ID
    - status: Current processing status (raw, processed, indexed)
    - uploaded_at: When the document was uploaded
    - processed_at: When processing was completed (if applicable)
    - file_size: Size of the uploaded file
    - chunks_count: Number of knowledge chunks created
    - law_sources_count: Number of law sources processed
    - articles_count: Number of articles processed
    """
    logger.info(f"📊 Getting upload status for document: {document_id}")
    
    try:
        from ..models.legal_knowledge import KnowledgeDocument, KnowledgeChunk, LawSource, LawArticle
        from sqlalchemy import select, func
        
        # Get document with counts
        result = await db.execute(
            select(
                KnowledgeDocument,
                func.count(KnowledgeChunk.id).label('chunks_count'),
                func.count(LawSource.id).label('law_sources_count'),
                func.count(LawArticle.id).label('articles_count')
            )
            .outerjoin(KnowledgeChunk, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .outerjoin(LawSource, LawSource.knowledge_document_id == KnowledgeDocument.id)
            .outerjoin(LawArticle, LawArticle.law_source_id == LawSource.id)
            .where(KnowledgeDocument.id == document_id)
            .group_by(KnowledgeDocument.id)
        )
        
        row = result.first()
        
        if not row:
            return create_error_response(
                message="Document not found",
                errors=[{"field": "document_id", "message": f"Document with ID {document_id} not found"}]
            )
        
        document, chunks_count, law_sources_count, articles_count = row
        
        # Get file size
        file_size = 0
        if document.file_path and os.path.exists(document.file_path):
            file_size = os.path.getsize(document.file_path)
        
        status_data = {
            "document_id": document.id,
            "title": document.title,
            "category": document.category,
            "status": document.status,
            "uploaded_at": document.uploaded_at,
            "processed_at": document.processed_at,
            "file_size_bytes": file_size,
            "file_hash": document.file_hash,
            "chunks_count": chunks_count or 0,
            "law_sources_count": law_sources_count or 0,
            "articles_count": articles_count or 0,
            "source_type": document.source_type,
            "uploaded_by": document.uploaded_by
        }
        
        logger.info(f"📊 Status retrieved: {document.title} - {document.status}")
        
        return create_success_response(
            message="Document status retrieved successfully",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get upload status: {e}")
        return create_error_response(
            message=f"Failed to retrieve document status: {str(e)}"
        )


@router.post("/debug-upload", response_model=ApiResponse[Dict[str, Any]])
async def debug_upload(
    file: UploadFile = File(..., description="Legal document file for debugging"),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Debug endpoint to inspect uploaded file content without processing.
    
    This endpoint helps troubleshoot JSON structure issues by showing:
    - File content preview
    - JSON structure analysis
    - Parsing validation results
    """
    logger.info(f"🔍 Debug upload for file: {file.filename}")
    
    try:
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            return create_error_response(
                message="Empty file",
                errors=[{"field": "file", "message": "File is empty"}]
            )
        
        # Try to decode as JSON
        try:
            json_data = json.loads(file_content.decode('utf-8'))
        except json.JSONDecodeError as e:
            return create_error_response(
                message="Invalid JSON format",
                errors=[{"field": "file", "message": f"JSON decode error: {str(e)}"}]
            )
        
        # Analyze JSON structure
        analysis = {
            "file_info": {
                "filename": file.filename,
                "size_bytes": len(file_content),
                "content_type": file.content_type
            },
            "json_analysis": {
                "data_type": str(type(json_data)),
                "is_dict": isinstance(json_data, dict),
                "is_list": isinstance(json_data, list),
                "top_level_keys": list(json_data.keys()) if isinstance(json_data, dict) else "N/A (not a dict)",
                "length": len(json_data) if hasattr(json_data, '__len__') else "N/A"
            },
            "structure_validation": {
                "has_law_sources": False,
                "has_law_source": False,
                "law_sources_type": None,
                "law_sources_count": 0,
                "expected_structure": "JSON should contain 'law_sources' array or be a single law source object"
            }
        }
        
        # Validate structure
        if isinstance(json_data, dict):
            if 'law_sources' in json_data:
                analysis["structure_validation"]["has_law_sources"] = True
                law_sources = json_data['law_sources']
                analysis["structure_validation"]["law_sources_type"] = str(type(law_sources))
                if isinstance(law_sources, list):
                    analysis["structure_validation"]["law_sources_count"] = len(law_sources)
                    analysis["structure_validation"]["expected_structure"] = "Found 'law_sources' as array (standard format)"
                else:
                    analysis["structure_validation"]["law_sources_count"] = 1
                    analysis["structure_validation"]["expected_structure"] = "Found 'law_sources' as single object (will be converted to array)"
                    
                    # Analyze the single law source object
                    first_source = law_sources
                    analysis["first_law_source"] = {
                        "type": str(type(first_source)),
                        "is_dict": isinstance(first_source, dict),
                        "keys": list(first_source.keys()) if isinstance(first_source, dict) else "N/A",
                        "has_name": isinstance(first_source, dict) and 'name' in first_source,
                        "has_articles": isinstance(first_source, dict) and 'articles' in first_source,
                        "articles_type": str(type(first_source.get('articles'))) if isinstance(first_source, dict) else "N/A",
                        "articles_count": len(first_source.get('articles', [])) if isinstance(first_source, dict) and isinstance(first_source.get('articles'), list) else 0
                    }
                    
                    # Analyze first article if exists
                    if isinstance(first_source, dict) and isinstance(first_source.get('articles'), list) and first_source['articles']:
                        first_article = first_source['articles'][0]
                        analysis["first_article"] = {
                            "type": str(type(first_article)),
                            "is_dict": isinstance(first_article, dict),
                            "keys": list(first_article.keys()) if isinstance(first_article, dict) else "N/A",
                            "has_text": isinstance(first_article, dict) and 'text' in first_article,
                            "has_article": isinstance(first_article, dict) and 'article' in first_article
                        }
            
            elif 'law_source' in json_data:
                analysis["structure_validation"]["has_law_source"] = True
                analysis["structure_validation"]["expected_structure"] = "Found 'law_source' (singular) instead of 'law_sources' (plural)"
        
        elif isinstance(json_data, list):
            analysis["structure_validation"]["expected_structure"] = "JSON is a list - should contain law source objects"
            if json_data:
                first_item = json_data[0]
                analysis["first_list_item"] = {
                    "type": str(type(first_item)),
                    "is_dict": isinstance(first_item, dict),
                    "keys": list(first_item.keys()) if isinstance(first_item, dict) else "N/A"
                }
        
        # Content preview (first 500 characters)
        content_preview = file_content.decode('utf-8')[:500]
        analysis["content_preview"] = content_preview + "..." if len(content_preview) == 500 else content_preview
        
        logger.info(f"✅ Debug analysis completed for: {file.filename}")
        
        return create_success_response(
            message="File debug analysis completed",
            data=analysis
        )
        
    except Exception as e:
        logger.error(f"❌ Debug upload failed: {e}")
        return create_error_response(
            message=f"Debug analysis failed: {str(e)}"
        )


@router.get("/supported-formats", response_model=ApiResponse[Dict[str, Any]])
async def get_supported_formats() -> ApiResponse[Dict[str, Any]]:
    """
    Get information about supported document formats and their capabilities.
    
    **Response Fields:**
    - supported_formats: List of supported file extensions
    - format_details: Detailed information about each format
    - processing_features: Available processing features
    - limitations: Current limitations and planned improvements
    """
    logger.info("📋 Getting supported document formats")
    
    try:
        formats_data = {
            "supported_formats": [".json", ".pdf", ".docx", ".doc", ".txt"],
            "format_details": {
                ".json": {
                    "status": "fully_supported",
                    "description": "Structured legal documents with law sources and articles",
                    "features": [
                        "Hierarchical parsing (Law Sources → Articles → Chunks)",
                        "Metadata extraction",
                        "Duplicate detection",
                        "Bulk database operations"
                    ],
                    "example_structure": {
                        "law_sources": [
                            {
                                "name": "Law Name",
                                "type": "law",
                                "articles": [
                                    {
                                        "article": "1",
                                        "title": "Article Title",
                                        "text": "Content...",
                                        "order_index": 1
                                    }
                                ]
                            }
                        ]
                    }
                },
                ".pdf": {
                    "status": "planned",
                    "description": "PDF legal documents",
                    "features": ["Text extraction", "Layout analysis", "OCR support"],
                    "planned_release": "Q2 2024"
                },
                ".docx": {
                    "status": "planned", 
                    "description": "Microsoft Word documents",
                    "features": ["Document structure parsing", "Table processing", "Formatting preservation"],
                    "planned_release": "Q2 2024"
                },
                ".txt": {
                    "status": "planned",
                    "description": "Plain text documents",
                    "features": ["Text structure detection", "Article identification", "Basic formatting"],
                    "planned_release": "Q1 2024"
                }
            },
            "processing_features": [
                "SHA-256 duplicate detection",
                "Hierarchical content organization",
                "Bulk database operations",
                "Comprehensive error handling",
                "Real-time processing statistics",
                "Metadata extraction and storage"
            ],
            "limitations": [
                "PDF, DOCX, and TXT parsing not yet implemented",
                "Maximum file size: 50MB",
                "No OCR support for scanned documents",
                "Limited text chunking strategies"
            ],
            "planned_improvements": [
                "Advanced NLP-based chunking",
                "Multi-language support",
                "OCR integration",
                "Document versioning",
                "Batch upload processing"
            ]
        }
        
        return create_success_response(
            message="Supported formats information retrieved successfully",
            data=formats_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get supported formats: {e}")
@router.get("/database/status", response_model=ApiResponse[Dict[str, Any]])
async def get_database_status(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Get status of both SQL and Chroma databases.
    
    **Response Fields:**
    - sql_database: Statistics from SQL database
    - chroma_database: Statistics from Chroma vectorstore
    - synchronization: Synchronization status between databases
    """
    logger.info("📊 Getting database status")
    
    try:
        upload_service = DocumentUploadService(db)
        status_data = await upload_service.get_database_status()
        
        logger.info("✅ Database status retrieved successfully")
        
        return create_success_response(
            message="Database status retrieved successfully",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get database status: {e}")
        return create_error_response(
            message=f"Failed to retrieve database status: {str(e)}"
        )


@router.post("/database/sync", response_model=ApiResponse[Dict[str, Any]])
async def sync_databases(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Synchronize SQL and Chroma databases.
    
    **Response Fields:**
    - success: Whether synchronization was successful
    - message: Synchronization result message
    - stats: Synchronization statistics
    """
    logger.info("🔄 Starting database synchronization")
    
    try:
        upload_service = DocumentUploadService(db)
        sync_result = await upload_service.sync_databases()
        
        if sync_result.get("success"):
            logger.info("✅ Database synchronization completed successfully")
            return create_success_response(
                message=sync_result.get("message", "Database synchronization completed"),
                data=sync_result
            )
        else:
            logger.error("❌ Database synchronization failed")
            return create_error_response(
                message=sync_result.get("message", "Database synchronization failed")
            )
        
    except Exception as e:
        logger.error(f"❌ Database synchronization error: {e}")
        return create_error_response(
            message=f"Database synchronization failed: {str(e)}"
        )


@router.put("/chunks/{chunk_id}", response_model=ApiResponse[Dict[str, Any]])
async def update_chunk(
    chunk_id: int,
    new_content: str = Form(..., description="New content for the chunk"),
    new_metadata: Optional[str] = Form(None, description="New metadata as JSON string"),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Update chunk content in both SQL and Chroma databases.
    
    **Parameters:**
    - chunk_id: ID of the chunk to update
    - new_content: New content for the chunk
    - new_metadata: Optional new metadata as JSON string
    
    **Response:**
    - Success: Update confirmation with chunk details
    - Error: Update failure information
    """
    logger.info(f"🔄 Updating chunk {chunk_id}")
    
    try:
        # Parse metadata if provided
        metadata = None
        if new_metadata:
            try:
                metadata = json.loads(new_metadata)
            except json.JSONDecodeError:
                return create_error_response(
                    message="Invalid metadata JSON format",
                    errors=[{"field": "new_metadata", "message": "Must be valid JSON"}]
                )
        
        upload_service = DocumentUploadService(db)
        success = await upload_service.update_chunk_content(chunk_id, new_content, metadata)
        
        if success:
            logger.info(f"✅ Chunk {chunk_id} updated successfully")
            return create_success_response(
                message=f"Chunk {chunk_id} updated successfully",
                data={"chunk_id": chunk_id, "updated": True}
            )
        else:
            logger.error(f"❌ Failed to update chunk {chunk_id}")
            return create_error_response(
                message=f"Failed to update chunk {chunk_id}"
            )
        
    except Exception as e:
        logger.error(f"❌ Error updating chunk {chunk_id}: {e}")
        return create_error_response(
            message=f"Failed to update chunk: {str(e)}"
        )


@router.delete("/chunks/{chunk_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_chunk(
    chunk_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete chunk from both SQL and Chroma databases.
    
    **Parameters:**
    - chunk_id: ID of the chunk to delete
    
    **Response:**
    - Success: Deletion confirmation
    - Error: Deletion failure information
    """
    logger.info(f"🗑️ Deleting chunk {chunk_id}")
    
    try:
        upload_service = DocumentUploadService(db)
        success = await upload_service.delete_chunk(chunk_id)
        
        if success:
            logger.info(f"✅ Chunk {chunk_id} deleted successfully")
            return create_success_response(
                message=f"Chunk {chunk_id} deleted successfully",
                data={"chunk_id": chunk_id, "deleted": True}
            )
        else:
            logger.error(f"❌ Failed to delete chunk {chunk_id}")
            return create_error_response(
                message=f"Failed to delete chunk {chunk_id}"
            )
        
    except Exception as e:
        logger.error(f"❌ Error deleting chunk {chunk_id}: {e}")
        return create_error_response(
            message=f"Failed to delete chunk: {str(e)}"
        )


@router.delete("/documents/{document_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete document and all its chunks from both SQL and Chroma databases.
    
    **Parameters:**
    - document_id: ID of the document to delete
    
    **Response:**
    - Success: Deletion confirmation with document details
    - Error: Deletion failure information
    """
    logger.info(f"🗑️ Deleting document {document_id}")
    
    try:
        upload_service = DocumentUploadService(db)
        success = await upload_service.delete_document(document_id)
        
        if success:
            logger.info(f"✅ Document {document_id} deleted successfully")
            return create_success_response(
                message=f"Document {document_id} and all chunks deleted successfully",
                data={"document_id": document_id, "deleted": True}
            )
        else:
            logger.error(f"❌ Failed to delete document {document_id}")
            return create_error_response(
                message=f"Failed to delete document {document_id}"
            )
        
    except Exception as e:
        logger.error(f"❌ Error deleting document {document_id}: {e}")
        return create_error_response(
            message=f"Failed to delete document: {str(e)}"
        )
