"""Legal Assistant API Router - Endpoints for legal document processing and search."""

import os
import shutil
import logging
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, Query
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/legal-assistant", tags=["Legal Assistant"])


@router.post("/documents/upload", response_model=ApiResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(default="other"),
    language: str = Form(default="ar"),
    notes: Optional[str] = Form(default=None),
    process_immediately: bool = Form(default=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a legal document for processing."""
    try:
        # Validate file extension
        allowed_ext = {'.pdf', '.docx', '.doc', '.txt'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_ext:
            return ApiResponse(
                success=False,
                message=f"Unsupported format. Allowed: {', '.join(allowed_ext)}",
                data=None,
                errors=[{"field": "file", "message": "Invalid file format"}]
            )
        
        # Save file
        import uuid
        upload_dir = Path("uploads/legal_documents")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / f"{uuid.uuid4()}{file_ext}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document
        service = LegalAssistantService(db)
        doc = await service.upload_document(
            file_path=str(file_path),
            original_filename=file.filename,
            title=title,
            document_type=document_type,
            language=language,
            uploaded_by_id=current_user.id,
            notes=notes,
            process_immediately=process_immediately
        )
        
        doc_response = DocumentResponse.from_orm(doc)
        return ApiResponse(
            success=True,
            message="Document uploaded successfully",
            data=doc_response.model_dump(),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[{"field": None, "message": str(e)}]
        )


@router.post("/documents/search", response_model=ApiResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Perform semantic search on legal documents."""
    try:
        service = LegalAssistantService(db)
        results, query_time = await service.search_documents(
            query=request.query,
            document_type=request.document_type,
            language=request.language,
            article_number=request.article_number,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        
        search_results = []
        for r in results:
            chunk_resp = DocumentChunkResponse.from_orm(r["chunk"])
            chunk_resp.similarity_score = r["similarity_score"]
            doc_resp = DocumentResponse.from_orm(r["document"])
            
            search_results.append(
                SearchResult(
                    chunk=chunk_resp,
                    document=doc_resp,
                    similarity_score=r["similarity_score"],
                    highlights=r["highlights"]
                )
            )
        
        response = SearchResponse(
            results=search_results,
            total_found=len(search_results),
            query_time_ms=query_time,
            query=request.query
        )
        
        return ApiResponse(
            success=True,
            message=f"Found {len(search_results)} results",
            data=response.model_dump(),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )


@router.get("/documents", response_model=ApiResponse)
async def get_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    document_type: Optional[str] = None,
    language: Optional[str] = None,
    processing_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of documents with pagination and filtering."""
    try:
        service = LegalAssistantService(db)
        docs, total = await service.get_documents(
            page=page,
            page_size=page_size,
            document_type=document_type,
            language=language,
            processing_status=processing_status
        )
        
        doc_responses = [DocumentResponse.from_orm(d) for d in docs]
        response = DocumentListResponse(
            documents=doc_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(docs)} documents",
            data=response.model_dump(),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )


@router.get("/documents/{document_id}", response_model=ApiResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific document."""
    try:
        service = LegalAssistantService(db)
        doc = await service.get_document(document_id)
        
        if not doc:
            return ApiResponse(
                success=False,
                message="Document not found",
                data=None,
                errors=[{"field": "document_id", "message": "Not found"}]
            )
        
        response_data = DocumentResponse.from_orm(doc)
        response_data.chunks_count = len(doc.chunks) if doc.chunks else 0
        
        return ApiResponse(
            success=True,
            message="Document retrieved",
            data=response_data.model_dump(),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Get document error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )


@router.put("/documents/{document_id}", response_model=ApiResponse)
async def update_document(
    document_id: int,
    update_request: DocumentUpdateRequest,
    reprocess: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update document metadata."""
    try:
        service = LegalAssistantService(db)
        doc = await service.update_document(
            document_id=document_id,
            title=update_request.title,
            document_type=update_request.document_type,
            language=update_request.language,
            notes=update_request.notes,
            reprocess=reprocess
        )
        
        if not doc:
            return ApiResponse(
                success=False,
                message="Document not found",
                data=None,
                errors=[]
            )
        
        return ApiResponse(
            success=True,
            message="Document updated",
            data=DocumentResponse.from_orm(doc).model_dump(),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Update error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )


@router.delete("/documents/{document_id}", response_model=ApiResponse)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and all its chunks."""
    try:
        service = LegalAssistantService(db)
        success = await service.delete_document(document_id)
        
        if not success:
            return ApiResponse(
                success=False,
                message="Document not found",
                data=None,
                errors=[]
            )
        
        return ApiResponse(
            success=True,
            message="Document deleted",
            data={"document_id": document_id, "deleted": True},
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )


@router.get("/documents/{document_id}/chunks", response_model=ApiResponse)
async def get_document_chunks(
    document_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chunks for a specific document."""
    try:
        service = LegalAssistantService(db)
        chunks = await service.get_document_chunks(
            document_id=document_id,
            page=page,
            page_size=page_size
        )
        
        chunk_responses = [DocumentChunkResponse.from_orm(c) for c in chunks]
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(chunks)} chunks",
            data={
                "chunks": [c.model_dump() for c in chunk_responses],
                "page": page,
                "page_size": page_size
            },
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Get chunks error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )


@router.get("/chunks/{chunk_id}", response_model=ApiResponse)
async def get_chunk(
    chunk_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific chunk."""
    try:
        service = LegalAssistantService(db)
        result = await service.get_chunk(chunk_id)
        
        if not result:
            return ApiResponse(
                success=False,
                message="Chunk not found",
                data=None,
                errors=[]
            )
        
        response = ChunkDetailResponse(
            chunk=DocumentChunkResponse.from_orm(result["chunk"]),
            document=DocumentResponse.from_orm(result["document"]),
            previous_chunk_id=result["previous_chunk_id"],
            next_chunk_id=result["next_chunk_id"]
        )
        
        return ApiResponse(
            success=True,
            message="Chunk retrieved",
            data=response.model_dump(),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Get chunk error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )


@router.get("/documents/{document_id}/progress", response_model=ApiResponse)
async def get_processing_progress(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get processing progress for a document."""
    try:
        service = LegalAssistantService(db)
        progress = await service.get_processing_progress(document_id)
        response = ProcessingProgressResponse(**progress)
        
        return ApiResponse(
            success=True,
            message="Progress retrieved",
            data=response.model_dump(),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Get progress error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )


@router.get("/statistics", response_model=ApiResponse)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system-wide statistics."""
    try:
        service = LegalAssistantService(db)
        stats = await service.get_statistics()
        response = DocumentStatsResponse(**stats)
        
        return ApiResponse(
            success=True,
            message="Statistics retrieved",
            data=response.model_dump(),
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )


@router.post("/documents/{document_id}/reprocess", response_model=ApiResponse)
async def reprocess_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reprocess an existing document."""
    try:
        service = LegalAssistantService(db)
        doc = await service.get_document(document_id)
        
        if not doc:
            return ApiResponse(
                success=False,
                message="Document not found",
                data=None,
                errors=[]
            )
        
        import asyncio
        asyncio.create_task(service.process_document(document_id))
        
        return ApiResponse(
            success=True,
            message="Reprocessing started",
            data={"document_id": document_id, "status": "processing"},
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Reprocess error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )

