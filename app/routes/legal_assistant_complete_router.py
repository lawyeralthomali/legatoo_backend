"""
Complete Legal Assistant API Router

This router provides comprehensive legal document management functionality including:
- Document upload with file validation
- Document retrieval with filtering and pagination
- Document update and deletion
- Document search functionality
- Document statistics and analytics
- Proper error handling and validation

All endpoints follow the unified API response format and include comprehensive documentation.
"""

import os
import shutil
import logging
import uuid
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, Query, HTTPException, Path as PathParam
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal_assistant_service import LegalAssistantService
from ..schemas.legal_assistant import (
    DocumentUploadRequest, DocumentResponse, DocumentListResponse,
    SearchRequest, SearchResponse, SearchResult, DocumentUpdateRequest,
    ProcessingProgressResponse, DocumentStatsResponse, ChunkDetailResponse,
    DocumentChunkResponse, DocumentTypeEnum, LanguageEnum, ProcessingStatusEnum
)
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..utils.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/legal-assistant", tags=["Legal Assistant"])

# ==================== DOCUMENT UPLOAD ====================

@router.post("/documents/upload", response_model=ApiResponse)
async def upload_legal_document(
    file: UploadFile = File(..., description="Legal document file (PDF, DOCX, TXT)"),
    title: str = Form(..., min_length=1, max_length=255, description="Document title"),
    document_type: DocumentTypeEnum = Form(default=DocumentTypeEnum.OTHER, description="Type of legal document"),
    language: LanguageEnum = Form(default=LanguageEnum.ARABIC, description="Document language"),
    notes: Optional[str] = Form(None, description="Additional notes about the document"),
    process_immediately: bool = Form(default=True, description="Process document immediately after upload"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a legal document for processing and indexing.
    
    Supports multiple file formats including PDF, DOCX, and TXT files.
    The document will be processed to extract text, create chunks, and generate embeddings
    for semantic search functionality.
    
    Args:
        file: Uploaded legal document file
        title: Descriptive title for the document
        document_type: Type of legal document (employment_contract, labor_law, etc.)
        language: Document language (ar, en, fr)
        notes: Optional additional notes about the document
        process_immediately: Whether to start processing immediately
        current_user: Current authenticated user
        
    Returns:
        ApiResponse containing uploaded document information and processing status
    """
    try:
        # Validate file
        if not file.filename:
            return create_error_response(
                message="No file provided",
                errors=[{"field": "file", "message": "File is required"}]
            )
        
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
        
        if file_ext not in allowed_extensions:
            return create_error_response(
                message=f"Unsupported file format: {file_ext}",
                errors=[{"field": "file", "message": f"Supported formats: {', '.join(allowed_extensions)}"}]
            )
        
        # Validate file size (10MB limit)
        file_size_limit = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > file_size_limit:
            return create_error_response(
                message="File size exceeds limit",
                errors=[{"field": "file", "message": "File size must be less than 10MB"}]
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Create upload directory
        upload_dir = Path("uploads/legal_documents")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Initialize service
        service = LegalAssistantService(db)
        
        # Upload document
        document = await service.upload_document(
            file_path=str(file_path),
            original_filename=file.filename,
            title=title,
            document_type=document_type.value,
            language=language.value,
            uploaded_by_id=current_user.sub,
            notes=notes,
            process_immediately=process_immediately
        )
        
        # Convert to response format
        doc_response = DocumentResponse.from_orm(document)
        
        logger.info(f"Document uploaded successfully: {document.id} - {title}")
        
        return create_success_response(
            message="Document uploaded successfully",
            data={
                "document": doc_response.model_dump(),
                "upload_info": {
                    "filename": file.filename,
                    "file_size": len(file_content),
                    "file_type": file_ext,
                    "process_immediately": process_immediately,
                    "uploaded_by": current_user.email
                }
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error in upload: {e}")
        return create_error_response(
            message="Invalid input data",
            errors=[{"field": None, "message": str(e)}]
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return create_error_response(
            message="Failed to upload document",
            errors=[{"field": None, "message": str(e)}]
        )

# ==================== DOCUMENT RETRIEVAL ====================

@router.get("/documents", response_model=ApiResponse)
async def get_legal_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of documents per page"),
    document_type: Optional[DocumentTypeEnum] = Query(default=None, description="Filter by document type"),
    language: Optional[LanguageEnum] = Query(default=None, description="Filter by language"),
    processing_status: Optional[ProcessingStatusEnum] = Query(default=None, description="Filter by processing status"),
    search: Optional[str] = Query(default=None, description="Search in document titles"),
    uploaded_by: Optional[int] = Query(default=None, description="Filter by uploader user ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve legal documents with filtering and pagination.
    
    Returns a paginated list of legal documents with optional filtering by type,
    language, processing status, and search terms. Supports comprehensive filtering
    for document management and discovery.
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of documents per page (1-100)
        document_type: Filter by document type
        language: Filter by document language
        processing_status: Filter by processing status
        search: Search term for document titles
        uploaded_by: Filter by uploader user ID
        current_user: Current authenticated user
        
    Returns:
        ApiResponse containing paginated document list with metadata
    """
    try:
        service = LegalAssistantService(db)
        
        # Get documents with filters
        documents, total = await service.get_documents(
            page=page,
            page_size=page_size,
            document_type=document_type.value if document_type else None,
            language=language.value if language else None,
            processing_status=processing_status.value if processing_status else None,
            search=search,
            uploaded_by_id=uploaded_by
        )
        
        # Convert to response format
        document_list = []
        for doc in documents:
            doc_response = DocumentResponse.from_orm(doc)
            document_list.append(doc_response.model_dump())
        
        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        
        return create_success_response(
            message=f"Retrieved {len(documents)} documents",
            data={
                "documents": document_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                },
                "filters": {
                    "document_type": document_type.value if document_type else None,
                    "language": language.value if language else None,
                    "processing_status": processing_status.value if processing_status else None,
                    "search": search,
                    "uploaded_by": uploaded_by
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        return create_error_response(
            message="Failed to retrieve documents",
            errors=[{"field": None, "message": str(e)}]
        )

@router.get("/documents/{document_id}", response_model=ApiResponse)
async def get_legal_document(
    document_id: int = PathParam(..., description="Document ID"),
    include_chunks: bool = Query(default=False, description="Include document chunks"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve a specific legal document by ID.
    
    Returns detailed information about a legal document including metadata,
    processing status, and optionally all associated chunks.
    
    Args:
        document_id: Unique identifier of the document
        include_chunks: Whether to include document chunks in response
        current_user: Current authenticated user
        
    Returns:
        ApiResponse containing document details and optional chunks
    """
    try:
        service = LegalAssistantService(db)
        
        # Get document
        document = await service.get_document(document_id)
        
        if not document:
            return create_error_response(
                message="Document not found",
                errors=[{"field": "document_id", "message": "Document not found"}]
            )
        
        # Convert to response format
        doc_response = DocumentResponse.from_orm(document)
        response_data = {"document": doc_response.model_dump()}
        
        # Include chunks if requested
        if include_chunks:
            chunks = await service.get_document_chunks(
                document_id=document_id,
                page=1,
                page_size=1000  # Get all chunks
            )
            
            chunk_list = []
            for chunk in chunks:
                chunk_response = DocumentChunkResponse.from_orm(chunk)
                chunk_list.append(chunk_response.model_dump())
            
            response_data["chunks"] = chunk_list
            response_data["chunks_count"] = len(chunks)
        
        return create_success_response(
            message="Document retrieved successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Get document error: {e}")
        return create_error_response(
            message="Failed to retrieve document",
            errors=[{"field": "document_id", "message": str(e)}]
        )

# ==================== DOCUMENT UPDATE ====================

@router.put("/documents/{document_id}", response_model=ApiResponse)
async def update_legal_document(
    document_id: int = PathParam(..., description="Document ID"),
    update_data: DocumentUpdateRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update legal document metadata.
    
    Allows updating document title, type, language, and notes. Does not affect
    the uploaded file or processing status.
    
    Args:
        document_id: Unique identifier of the document
        update_data: Updated document metadata
        current_user: Current authenticated user
        
    Returns:
        ApiResponse containing updated document information
    """
    try:
        service = LegalAssistantService(db)
        
        # Check if document exists
        document = await service.get_document(document_id)
        if not document:
            return create_error_response(
                message="Document not found",
                errors=[{"field": "document_id", "message": "Document not found"}]
            )
        
        # Update document
        updated_document = await service.update_document(
            document_id=document_id,
            title=update_data.title,
            document_type=update_data.document_type.value if update_data.document_type else None,
            language=update_data.language.value if update_data.language else None,
            notes=update_data.notes
        )
        
        if not updated_document:
            return create_error_response(
                message="Failed to update document",
                errors=[{"field": None, "message": "Update operation failed"}]
            )
        
        # Convert to response format
        doc_response = DocumentResponse.from_orm(updated_document)
        
        logger.info(f"Document updated successfully: {document_id}")
        
        return create_success_response(
            message="Document updated successfully",
            data={"document": doc_response.model_dump()}
        )
        
    except Exception as e:
        logger.error(f"Update document error: {e}")
        return create_error_response(
            message="Failed to update document",
            errors=[{"field": None, "message": str(e)}]
        )

# ==================== DOCUMENT DELETION ====================

@router.delete("/documents/{document_id}", response_model=ApiResponse)
async def delete_legal_document(
    document_id: int = PathParam(..., description="Document ID"),
    delete_file: bool = Query(default=True, description="Delete file from filesystem"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a legal document and all associated data.
    
    Permanently removes the document, all its chunks, embeddings, and optionally
    the file from the filesystem. This action is irreversible.
    
    Args:
        document_id: Unique identifier of the document
        delete_file: Whether to delete the file from filesystem
        current_user: Current authenticated user
        
    Returns:
        ApiResponse containing deletion confirmation
    """
    try:
        service = LegalAssistantService(db)
        
        # Get document details before deletion
        document = await service.get_document(document_id)
        if not document:
            return create_error_response(
                message="Document not found",
                errors=[{"field": "document_id", "message": "Document not found"}]
            )
        
        # Extract file path and chunks count
        file_path = Path(document.file_path) if document else None
        chunks_count = len(document.chunks) if document and document.chunks else 0
        
        # Delete from database
        success = await service.delete_document(document_id)
        
        if not success:
            return create_error_response(
                message="Failed to delete document from database",
                errors=[{"field": "document_id", "message": "Database deletion failed"}]
            )
        
        # Delete file if requested and it exists
        file_deleted = False
        if delete_file and file_path and file_path.exists():
            try:
                file_path.unlink()
                file_deleted = True
                logger.info(f"Deleted file: {file_path}")
            except Exception as file_error:
                logger.error(f"Failed to delete file {file_path}: {file_error}")
        
        logger.info(f"Document deleted successfully: {document_id}")
        
        return create_success_response(
            message="Document deleted successfully",
            data={
                "document_id": document_id,
                "document_title": document.title,
                "chunks_deleted": chunks_count,
                "file_deleted": file_deleted,
                "deleted_by": current_user.email
            }
        )
        
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        return create_error_response(
            message="Failed to delete document",
            errors=[{"field": None, "message": str(e)}]
        )

# ==================== DOCUMENT SEARCH ====================

@router.post("/documents/search", response_model=ApiResponse)
async def search_legal_documents(
    search_request: SearchRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search legal documents using semantic search.
    
    Performs semantic search across all processed legal documents using embeddings.
    Returns relevant chunks with similarity scores and highlighting.
    
    Args:
        search_request: Search parameters including query and filters
        current_user: Current authenticated user
        
    Returns:
        ApiResponse containing search results with similarity scores
    """
    try:
        service = LegalAssistantService(db)
        
        # Perform semantic search
        search_results = await service.search_documents(
            query=search_request.query,
            document_type=search_request.document_type.value if search_request.document_type else None,
            language=search_request.language.value if search_request.language else None,
            article_number=search_request.article_number,
            limit=search_request.limit,
            similarity_threshold=search_request.similarity_threshold
        )
        
        # Convert to response format
        results = []
        for result in search_results:
            chunk_response = DocumentChunkResponse.from_orm(result['chunk'])
            doc_response = DocumentResponse.from_orm(result['document'])
            
            search_result = SearchResult(
                chunk=chunk_response,
                document=doc_response,
                similarity_score=result['similarity_score'],
                highlights=result.get('highlights', [])
            )
            results.append(search_result.model_dump())
        
        return create_success_response(
            message=f"Found {len(results)} results",
            data={
                "results": results,
                "total_found": len(results),
                "query": search_request.query,
                "filters": {
                    "document_type": search_request.document_type.value if search_request.document_type else None,
                    "language": search_request.language.value if search_request.language else None,
                    "article_number": search_request.article_number,
                    "similarity_threshold": search_request.similarity_threshold
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Search documents error: {e}")
        return create_error_response(
            message="Failed to search documents",
            errors=[{"field": None, "message": str(e)}]
        )

# ==================== DOCUMENT STATISTICS ====================

@router.get("/documents/statistics", response_model=ApiResponse)
async def get_legal_document_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive statistics about legal documents.
    
    Returns statistics including total documents, chunks, processing status,
    and breakdown by document type and language.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        ApiResponse containing document statistics
    """
    try:
        service = LegalAssistantService(db)
        
        # Get statistics
        stats = await service.get_document_statistics()
        
        return create_success_response(
            message="Statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        return create_error_response(
            message="Failed to retrieve statistics",
            errors=[{"field": None, "message": str(e)}]
        )

# ==================== DOCUMENT PROCESSING ====================

@router.get("/documents/{document_id}/processing-status", response_model=ApiResponse)
async def get_document_processing_status(
    document_id: int = PathParam(..., description="Document ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the processing status of a legal document.
    
    Returns detailed information about the document's processing status,
    progress percentage, and any errors encountered.
    
    Args:
        document_id: Unique identifier of the document
        current_user: Current authenticated user
        
    Returns:
        ApiResponse containing processing status information
    """
    try:
        service = LegalAssistantService(db)
        
        # Get document
        document = await service.get_document(document_id)
        if not document:
            return create_error_response(
                message="Document not found",
                errors=[{"field": "document_id", "message": "Document not found"}]
            )
        
        # Get processing progress
        progress = await service.get_processing_progress(document_id)
        
        return create_success_response(
            message="Processing status retrieved successfully",
            data={
                "document_id": document_id,
                "document_title": document.title,
                "processing_status": document.processing_status,
                "is_processed": document.is_processed,
                "progress": progress
            }
        )
        
    except Exception as e:
        logger.error(f"Get processing status error: {e}")
        return create_error_response(
            message="Failed to retrieve processing status",
            errors=[{"field": None, "message": str(e)}]
        )

@router.post("/documents/{document_id}/reprocess", response_model=ApiResponse)
async def reprocess_legal_document(
    document_id: int = PathParam(..., description="Document ID"),
    force_reprocess: bool = Query(default=False, description="Force reprocessing even if already processed"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger reprocessing of a legal document.
    
    Starts asynchronous reprocessing of a document, regenerating chunks and embeddings.
    Useful for fixing processing errors or updating with new models.
    
    Args:
        document_id: Unique identifier of the document
        force_reprocess: Whether to reprocess even if already processed
        current_user: Current authenticated user
        
    Returns:
        ApiResponse containing reprocessing status
    """
    try:
        service = LegalAssistantService(db)
        
        # Get document to verify it exists
        document = await service.get_document(document_id)
        if not document:
            return create_error_response(
                message="Document not found",
                errors=[{"field": "document_id", "message": "Document not found"}]
            )
        
        # Check if already processed and not forcing
        if document.processing_status == "done" and not force_reprocess:
            return create_success_response(
                message="Document already processed successfully. Use force_reprocess=true to override.",
                data={
                    "document_id": document_id,
                    "status": "already_processed",
                    "processing_status": document.processing_status
                }
            )
        
        # Start reprocessing
        asyncio.create_task(service.process_document(document_id))
        
        logger.info(f"Reprocessing started for document {document_id}")
        
        return create_success_response(
            message="Document reprocessing started successfully",
            data={
                "document_id": document_id,
                "status": "processing_started",
                "document_title": document.title,
                "force_reprocess": force_reprocess
            }
        )
        
    except Exception as e:
        logger.error(f"Reprocess document error: {e}")
        return create_error_response(
            message="Failed to start reprocessing",
            errors=[{"field": None, "message": str(e)}]
        )

# ==================== DOCUMENT DOWNLOAD ====================

@router.get("/documents/{document_id}/download")
async def download_legal_document(
    document_id: int = PathParam(..., description="Document ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download the original legal document file.
    
    Serves the original document file from the filesystem for download.
    Supports PDF, DOCX, and other document formats.
    
    Args:
        document_id: Unique identifier of the document
        current_user: Current authenticated user
        
    Returns:
        FastAPI Response object with file download
    """
    try:
        service = LegalAssistantService(db)
        
        # Get document
        document = await service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = Path(document.file_path)
        
        if not file_path.exists():
            logger.error(f"Document file not found: {file_path}")
            raise HTTPException(status_code=404, detail="Document file not found on disk")
        
        # Determine content type
        file_ext = file_path.suffix.lower()
        content_type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain'
        }
        content_type = content_type_map.get(file_ext, 'application/octet-stream')
        
        # Generate filename
        filename = document.title.replace(' ', '_') + file_ext
        
        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download document error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
