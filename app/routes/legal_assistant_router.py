"""Legal Assistant API Router - Admin Endpoints for legal document processing and management."""

import os
import shutil
import logging
import uuid
import asyncio
from typing import Optional, List
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..services.legal_assistant_service import LegalAssistantService
from ..schemas.legal_assistant import (
    DocumentUploadRequest, DocumentResponse, DocumentListResponse,
    SearchRequest, SearchResponse, SearchResult, DocumentUpdateRequest,
    ProcessingProgressResponse, DocumentStatsResponse, ChunkDetailResponse,
    DocumentChunkResponse
)
from ..schemas.response import ApiResponse
from ..utils.auth import get_current_user
from ..models.user import User
from ..schemas.response import ErrorDetail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/legal-assistant", tags=["Legal Assistant"])


# ==================== ADMIN ENDPOINTS ====================

@router.get("/documents", response_model=ApiResponse, tags=["Admin"])
async def admin_list_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of documents per page"),
    document_type: Optional[str] = Query(default=None, description="Filter by document type"),
    processing_status: Optional[str] = Query(default=None, description="Filter by processing status"),
    uploaded_by: Optional[int] = Query(default=None, description="Filter by uploader user ID"),
    language: Optional[str] = Query(default=None, description="Filter by document language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint to list legal documents with pagination and filtering.
    
    Returns paginated list of documents with metadata for admin management.
    Supports filtering by document type, processing status, uploader, and language.
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of documents per page (1-100)
        document_type: Filter by document type (employment_contract, labor_law, etc.)
        processing_status: Filter by status (pending, processing, done, error)
        uploaded_by: Filter by uploader user ID
        language: Filter by document language (ar, en, fr)
        
    Returns:
        ApiResponse containing paginated document list with metadata
    """
    try:
        service = LegalAssistantService(db)
        
        # Fetch documents with filters
        docs, total = await service.get_documents(
            page=page,
            page_size=page_size,
            document_type=document_type,
            language=language,
            processing_status=processing_status
        )
        
        # Convert to response format
        document_list = []
        for doc in docs:
            doc_data = DocumentResponse.from_orm(doc)
            # Add admin-specific fields
            admin_doc = {
                "id": doc_data.id,
                "title": doc_data.title,
                "document_type": doc_data.document_type,
                "language": doc_data.language,
                "uploaded_by_id": doc_data.uploaded_by_id,
                "created_at": doc_data.created_at,
                "processing_status": doc_data.processing_status,
                "is_processed": doc_data.is_processed,
                "notes": doc_data.notes,
                "file_path": doc_data.file_path,
                "chunks_count": len(doc.chunks) if doc.chunks else 0
            }
            document_list.append(admin_doc)
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(docs)} documents",
            data={
                "documents": document_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                },
                "filters": {
                    "document_type": document_type,
                    "processing_status": processing_status,
                    "uploaded_by": uploaded_by,
                    "language": language
                }
            },
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Admin list documents error: {e}")
        return ApiResponse(
            success=False,
            message=f"Failed to retrieve documents: {str(e)}",
            data=None,
            errors=[{"field": None, "message": str(e)}]
        )


@router.get("/documents/{document_id}", response_model=ApiResponse, tags=["Admin"])
async def admin_get_document_details(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint to get detailed document information including all chunks.
    
    Returns comprehensive document metadata, processing status, and all associated chunks
    for administrative purposes.
    
    Args:
        document_id: Unique identifier of the document
        
    Returns:
        ApiResponse containing document details and chunks list
    """
    try:
        service = LegalAssistantService(db)
        
        # Get document details
        doc = await service.get_document(document_id)
        
        if not doc:
            return ApiResponse(
                success=False,
                message="Document not found",
                data=None,
                errors=[{"field": "document_id", "message": "Document not found"}]
            )
        
        # Convert document to response format
        doc_response = DocumentResponse.from_orm(doc)
        
        # Get all chunks for this document
        chunks = await service.get_document_chunks(
            document_id=document_id,
            page=1,
            page_size=1000  # Get all chunks for admin view
        )
        
        # Convert chunks to response format
        chunk_list = []
        for chunk in chunks:
            chunk_data = {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "article_number": chunk.article_number,
                "section_title": chunk.section_title,
                "keywords": chunk.keywords or [],
                "page_number": getattr(chunk, 'page_number', None),
                "source_reference": getattr(chunk, 'source_reference', None),
                "has_embedding": bool(chunk.embedding),
                "created_at": chunk.created_at.isoformat() if chunk.created_at else None
            }
            chunk_list.append(chunk_data)
        
        # Comprehensive document details
        document_details = {
            "document": doc_response.model_dump(),
            "chunks": chunk_list,
            "statistics": {
                "total_chunks": len(chunks),
                "chunks_with_embeddings": sum(1 for c in chunks if c.embedding),
                "chunks_with_article_numbers": sum(1 for c in chunks if c.article_number),
                "chunks_with_section_titles": sum(1 for c in chunks if c.section_title),
                "keywords_extracted": sum(len(c.keywords or []) for c in chunks)
            }
        }
        
        return ApiResponse(
            success=True,
            message="Document details retrieved successfully",
            data=document_details,
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Admin get document details error: {e}")
        return ApiResponse(
            success=False,
            message=f"Failed to retrieve document details: {str(e)}",
            data=None,
            errors=[{"field": "document_id", "message": str(e)}]
        )


@router.get("/documents/{document_id}/download", tags=["Admin"])
async def admin_download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint to download the original uploaded document file.
    
    Serves the original document file from the filesystem for admin download.
    Handles file not found errors and supports PDF, DOCX, and other document formats.
    
    Args:
        document_id: Unique identifier of the document to download
        
    Returns:
        FastAPI Response object with file download or error message
    """
    try:
        service = LegalAssistantService(db)
        
        # Get document details
        doc = await service.get_document(document_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = Path(doc.file_path)
        
        if not file_path.exists():
            logger.error(f"Document file not found: {file_path}")
            raise HTTPException(status_code=404, detail="Document file not found on disk")
        
        # Determine content type based on file extension
        file_ext = file_path.suffix.lower()
        content_type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain'
        }
        content_type = content_type_map.get(file_ext, 'application/octet-stream')
        
        # Generate filename
        filename = doc.title.replace(' ', '_') + file_ext
        
        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Admin download document error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.post("/documents/{document_id}/reprocess", response_model=ApiResponse, tags=["Admin"])
async def admin_reprocess_document(
    document_id: int,
    force_reprocess: bool = Query(default=False, description="Force reprocessing even if already processed"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint to trigger document reprocessing pipeline.
    
    Starts asynchronous reprocessing of a document, regenerating chunks and embeddings.
    Useful for admin maintenance, model updates, or fixing processing errors.
    
    Args:
        document_id: Unique identifier of the document to reprocess
        force_reprocess: If True, reprocess even if document was already processed
        
    Returns:
        ApiResponse with processing status and document information
    """
    try:
        service = LegalAssistantService(db)
        
        # Get document to verify it exists
        doc = await service.get_document(document_id)
        
        if not doc:
            return ApiResponse(
                success=False,
                message="Document not found",
                data=None,
                errors=[{"field": "document_id", "message": "Document not found"}]
            )
        
        # Check if already processed and not forcing
        if doc.processing_status == "done" and not force_reprocess:
            return ApiResponse(
                success=True,
                message="Document already processed successfully. Use force_reprocess=true to override.",
                data={
                    "document_id": document_id,
                    "status": "already_processed",
                    "processing_status": doc.processing_status,
                    "is_processed": doc.is_processed
                },
                errors=[]
            )
        
        # Start asynchronous reprocessing
        asyncio.create_task(service.process_document(document_id))
        
        logger.info(f"Admin initiated reprocessing for document {document_id}")
        
        return ApiResponse(
            success=True,
            message="Document reprocessing started successfully",
            data={
                "document_id": document_id,
                "status": "processing_started",
                "title": doc.title,
                "force_reprocess": force_reprocess,
                "timestamp": doc.created_at.isoformat() if doc.created_at else None
            },
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Admin reprocess document error: {e}")
        return ApiResponse(
            success=False,
            message=f"Failed to start reprocessing: {str(e)}",
            data=None,
            errors=[{"field": "document_id", "message": str(e)}]
        )


@router.delete("/documents/{document_id}", response_model=ApiResponse, tags=["Admin"])
async def admin_delete_document(
    document_id: int,
    delete_file: bool = Query(default=True, description="Delete file from filesystem"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint to permanently delete a document and all associated data.
    
    Removes the document, all its chunks, embeddings, and optionally the file from disk.
    This action is irreversible and should be used with caution.
    
    Args:
        document_id: Unique identifier of the document to delete
        delete_file: If True, also delete the physical file from filesystem
        
    Returns:
        ApiResponse with deletion confirmation and details
    """
    try:
        service = LegalAssistantService(db)
        
        # Get document details before deletion
        doc = await service.get_document(document_id)
        
        if not doc:
            return ApiResponse(
                success=False,
                message="Document not found",
                data=None,
                errors=[{"field": "document_id", "message": "Document not found"}]
            )
        
        # Extract file path before deletion
        file_path = Path(doc.file_path) if doc else None
        chunks_count = len(doc.chunks) if doc and doc.chunks else 0
        
        # Delete from database
        success = await service.delete_document(document_id)
        
        if not success:
            return ApiResponse(
                success=False,
                message="Failed to delete document from database",
                data=None,
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
        
        logger.info(f"Admin deleted document {document_id} with {chunks_count} chunks")
        
        return ApiResponse(
            success=True,
            message="Document deleted successfully",
            data={
                "document_id": document_id,
                "deleted": True,
                "document_title": doc.title,
                "chunks_deleted": chunks_count,
                "file_deleted": file_deleted,
                "file_path": str(file_path) if file_path else None,
                "timestamp": doc.created_at.isoformat() if doc.created_at else None
            },
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Admin delete document error: {e}")
        return ApiResponse(
            success=False,
            message=f"Failed to delete document: {str(e)}",
            data=None,
            errors=[{"field": "document_id", "message": str(e)}]
        )


@router.get("/documents/{document_id}/chunks", response_model=ApiResponse, tags=["Admin"])
async def admin_get_document_chunks(
    document_id: int,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Number of chunks per page"),
    include_embeddings: bool = Query(default=False, description="Include embedding data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint to get detailed chunks information for a specific document.
    
    Returns paginated list of document chunks with detailed metadata for admin analysis.
    Can optionally include embedding vectors for debugging purposes.
    
    Args:
        document_id: Unique identifier of the document
        page: Page number (starts from 1)
        page_size: Number of chunks per page (1-200)
        include_embeddings: If True, include embedding vectors in response
        
    Returns:
        ApiResponse containing paginated chunks with metadata
    """
    try:
        service = LegalAssistantService(db)
        
        # Verify document exists
        doc = await service.get_document(document_id)
        
        if not doc:
            return ApiResponse(
                success=False,
                message="Document not found",
                data=None,
                errors=[{"field": "document_id", "message": "Document not found"}]
            )
        
        # Get chunks with pagination
        chunks = await service.get_document_chunks(
            document_id=document_id,
            page=page,
            page_size=page_size
        )
        
        # Convert chunks to detailed response format
        chunk_list = []
        for chunk in chunks:
            chunk_data = {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "content_length": len(chunk.content),
                "article_number": chunk.article_number,
                "section_title": chunk.section_title,
                "keywords": chunk.keywords or [],
                "keywords_count": len(chunk.keywords or []),
                "page_number": getattr(chunk, 'page_number', None),
                "source_reference": getattr(chunk, 'source_reference', None),
                "has_embedding": bool(chunk.embedding),
                "embedding_dimension": len(chunk.embedding) if chunk.embedding else 0,
                "created_at": chunk.created_at.isoformat() if chunk.created_at else None
            }

            if include_embeddings and chunk.embedding:
                chunk_data["embedding"] = chunk.embedding[:10] if len(chunk.embedding) > 10 else chunk.embedding  # Limit for display
            
            chunk_list.append(chunk_data)
        
        # Get total chunks count for pagination
        total_chunks = len(doc.chunks) if doc.chunks else 0
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(chunks)} chunks",
            data={
                "chunks": chunk_list,
                "document_id": document_id,
                "document_title": doc.title,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total_chunks,
                    "total_pages": (total_chunks + page_size - 1) // page_size
                },
                "statistics": {
                    "chunks_with_embeddings": sum(1 for c in chunks if c.embedding),
                    "average_content_length": sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0,
                    "chunks_with_article_numbers": sum(1 for c in chunks if c.article_number),
                    "chunks_with_section_titles": sum(1 for c in chunks if c.section_title)
                }
            },
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Admin get document chunks error: {e}")
        return ApiResponse(
            success=False,
            message=f"Failed to retrieve chunks: {str(e)}",
            data=None,
            errors=[{"field": "document_id", "message": str(e)}]
        )


@router.post("/documents/upload", response_model=ApiResponse, tags=["Admin"])
async def admin_upload_multiple_documents(
    files: List[UploadFile] = File(...),
    titles: Optional[List[str]] = Form(default=None),
    document_type: str = Form(default="other"),
    language: str = Form(default="ar"),
    notes: Optional[str] = Form(default="Admin upload"),
    process_immediately: bool = Form(default=True),
    assign_to_user: Optional[int] = Form(default=None, description="Assign documents to specific user"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint for bulk upload of multiple legal documents.
    
    Enables administrators to upload multiple documents at once with batch processing.
    Supports automatic title generation and can assign documents to specific users.
    
    Args:
        files: List of files to upload (required)
        titles: Optional list of custom titles for each file
        document_type: Document type for all uploaded files
        language: Language for all uploaded files
        notes: Notes to apply to all uploaded files
        process_immediately: Whether to start processing immediately
        assign_to_user: Optional user ID to assign uploaded documents to
        
    Returns:
        ApiResponse containing list of uploaded documents with status
    """
    try:
        # Validate files list
        if not files or len(files) == 0:
            return ApiResponse(
                success=False,
                message="At least one file is required",
                data=None,
                errors=[{"field": "files", "message": "No files provided"}]
            )
        
        # Validate admin file extensions
        allowed_ext = {'.pdf', '.docx', '.doc', '.txt'}
        
        uploaded_documents = []
        errors = []
        
        # Process each file individually
        for i, file in enumerate(files):
            try:
                # Validate file extension
                file_ext = Path(file.filename).suffix.lower()
                
                if file_ext not in allowed_ext:
                    errors.append({
                        "field": f"files[{i}]",
                        "message": f"Unsupported format '{file_ext}' for file '{file.filename}'. Allowed: {', '.join(allowed_ext)}"
                    })
                    continue
                
                # Generate title from filename or use provided
                title = None
                if titles and i < len(titles) and titles[i].strip():
                    title = titles[i].strip()
                
                if not title:
                    filename_stem = Path(file.filename).stem
                    title = filename_stem if filename_stem else f"Admin Upload - Document {i + 1}"
                
                # Save file
                upload_dir = Path("uploads/legal_documents")
                upload_dir.mkdir(parents=True, exist_ok=True)
                file_path = upload_dir / f"{uuid.uuid4()}{file_ext}"
                
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Create document with admin context
                service = LegalAssistantService(db)
                uploader_id = assign_to_user if assign_to_user else current_user.sub
                admin_notes = f"{notes} [Uploaded by: {current_user.email}]"
                
                doc = await service.upload_document(
                    file_path=str(file_path),
                    original_filename=file.filename,
                    title=title,
                    document_type=document_type,
                    language=language,
                    uploaded_by_id=uploader_id,
                    notes=admin_notes,
                    process_immediately=process_immediately
                )
                
                doc_response = DocumentResponse.from_orm(doc)
                uploaded_documents.append(doc_response.model_dump())
                
                logger.info(f"Admin uploaded document: {file.filename} -> {title}")
                
            except Exception as file_error:
                logger.error(f"Error processing file {file.filename}: {file_error}")
                errors.append({
                    "field": f"files[{i}]",
                    "message": f"Failed to process file '{file.filename}': {str(file_error)}"
                })
        
        # Return comprehensive results
        if errors:
            # Partial success with errors
            success_count = len(uploaded_documents)
            error_count = len(errors)
            return ApiResponse(
                success=success_count > 0,
                message=f"Uploaded {success_count} document(s), {error_count} error(s)",
                data={
                    "uploaded_documents": uploaded_documents,
                    "uploaded_count": success_count,
                    "error_count": error_count,
                    "errors": errors
                },
                errors=errors
            )
        else:
            # All files uploaded successfully
            return ApiResponse(
                success=True,
                message=f"Successfully uploaded {len(uploaded_documents)} document(s)",
                data={
                    "uploaded_documents": uploaded_documents,
                    "uploaded_count": len(uploaded_documents),
                    "admin_info": {
                        "uploaded_by_admin": current_user.email,
                        "assigned_to_user": assign_to_user,
                        "process_immediately": process_immediately,
                        "timestamp": doc.created_at.isoformat() if "doc" in locals() else None
                    }
                },
                errors=[]
            )
        
    except Exception as e:
        logger.error(f"Admin upload multiple documents error: {e}")
        return ApiResponse(
            success=False,
            message=f"Bulk upload failed: {str(e)}",
            data=None,
            errors=[{"field": None, "message": str(e)}]
        )