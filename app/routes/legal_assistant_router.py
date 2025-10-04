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
    """
    Upload a legal document for processing.
    
    ✅ Phase 3 & 4: Now supports PDF, DOCX, Images (OCR), TXT
    """
    try:
        # ✅ UPDATED: Support more formats including images for OCR
        allowed_ext = {'.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png'}
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
            uploaded_by_id=current_user.sub,
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
            # Use proper validation instead of from_orm to trigger RTL processing
            chunk_data = {
                "id": r["chunk"].id,
                "chunk_index": r["chunk"].chunk_index,
                "content": r["chunk"].content,
                "article_number": r["chunk"].article_number,
                "section_title": r["chunk"].section_title,
                "keywords": r["chunk"].keywords or [],
                "similarity_score": r["similarity_score"]
            }
            chunk_resp = DocumentChunkResponse(**chunk_data)
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
        
        # Use proper validation instead of from_orm to trigger RTL processing
        chunk_responses = []
        for c in chunks:
            chunk_data = {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "content": c.content,
                "article_number": c.article_number,
                "section_title": c.section_title,
                "keywords": c.keywords or []
            }
            chunk_resp = DocumentChunkResponse(**chunk_data)
            chunk_responses.append(chunk_resp)
        
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
        
        # Use proper validation instead of from_orm to trigger RTL processing
        chunk_data = {
            "id": result["chunk"].id,
            "chunk_index": result["chunk"].chunk_index,
            "content": result["chunk"].content,
            "article_number": result["chunk"].article_number,
            "section_title": result["chunk"].section_title,
            "keywords": result["chunk"].keywords or []
        }
        chunk_resp = DocumentChunkResponse(**chunk_data)
        
        response = ChunkDetailResponse(
            chunk=chunk_resp,
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


@router.post("/test-arabic-hardcoded", response_model=ApiResponse)
async def test_arabic_hardcoded(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test Arabic text processing with hardcoded Arabic text.
    """
    try:
        from ..utils.arabic_text_processor import ArabicTextProcessor
        
        # Hardcoded Arabic text to avoid encoding issues
        arabic_text = "مرحبا بالعالم"  # Hello World in Arabic
        
        # Test the processing pipeline
        result = ArabicTextProcessor.format_arabic_chunk(arabic_text, "ar")
        
        # Test chunk response
        chunk_data = {
            "id": 1,
            "chunk_index": 0,
            "content": arabic_text,
            "article_number": None,
            "section_title": None,
            "keywords": []
        }
        
        chunk_response = DocumentChunkResponse(**chunk_data)
        
        return ApiResponse(
            success=True,
            message="Arabic text processing test completed",
            data={
                "original_text": arabic_text,
                "processor_result": result,
                "chunk_response": chunk_response.model_dump()
            },
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Arabic hardcoded test error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )
async def test_chunk_response(
    text: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test DocumentChunkResponse with Arabic text processing.
    """
    try:
        # Create chunk data similar to what comes from database
        chunk_data = {
            "id": 1,
            "chunk_index": 0,
            "content": text,
            "article_number": None,
            "section_title": None,
            "keywords": []
        }
        
        # Create DocumentChunkResponse (this should trigger the validator)
        chunk_response = DocumentChunkResponse(**chunk_data)
        
        return ApiResponse(
            success=True,
            message="DocumentChunkResponse test completed",
            data={
                "original_text": text,
                "chunk_response": chunk_response.model_dump()
            },
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Chunk response test error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )
async def test_arabic_processing(
    text: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint for Arabic text processing.
    """
    try:
        from ..utils.arabic_text_processor import ArabicTextProcessor
        
        # Test Arabic text processing
        result = ArabicTextProcessor.format_arabic_chunk(text, "ar")
        
        return ApiResponse(
            success=True,
            message="Arabic text processing test completed",
            data={
                "original_text": text,
                "is_arabic": result['is_rtl'],
                "text_direction": result['language'],
                "formatted_content": result['formatted_content'],
                "normalized_content": result['content']
            },
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Arabic test error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[]
        )
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


@router.get("/debug/extracted-text/{document_id}", response_model=ApiResponse)
async def get_extracted_text_files(
    document_id: int,
    file_type: str = Query(default="all", description="Type of file to retrieve: raw, cleaned, chunks, or all"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Debug endpoint to view extracted text files.
    
    This endpoint allows you to see how Arabic text looks after extraction,
    cleaning, and chunking processes.
    
    Args:
        document_id: ID of the document
        file_type: Type of file to retrieve (raw, cleaned, chunks, all)
    """
    try:
        from pathlib import Path
        import os
        
        # Check if document exists
        service = LegalAssistantService(db)
        doc = await service.get_document(document_id)
        
        if not doc:
            return ApiResponse(
                success=False,
                message="Document not found",
                data=None,
                errors=[{"field": "document_id", "message": "Document does not exist"}]
            )
        
        extracted_text_dir = Path("uploads/extracted_text")
        
        if not extracted_text_dir.exists():
            return ApiResponse(
                success=False,
                message="No extracted text files found",
                data=None,
                errors=[{"field": "extracted_text_dir", "message": "Extracted text directory does not exist"}]
            )
        
        files_info = []
        
        # Define file patterns
        file_patterns = {
            "raw": f"document_{document_id}_raw.txt",
            "cleaned": f"document_{document_id}_cleaned.txt", 
            "chunks": f"document_{document_id}_chunks.txt"
        }
        
        if file_type == "all":
            files_to_check = list(file_patterns.values())
        elif file_type in file_patterns:
            files_to_check = [file_patterns[file_type]]
        else:
            return ApiResponse(
                success=False,
                message="Invalid file_type. Use: raw, cleaned, chunks, or all",
                data=None,
                errors=[{"field": "file_type", "message": "Invalid file type specified"}]
            )
        
        for filename in files_to_check:
            file_path = extracted_text_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    file_type_name = filename.split('_')[-1].replace('.txt', '')
                    files_info.append({
                        "file_type": file_type_name,
                        "filename": filename,
                        "file_path": str(file_path),
                        "size_bytes": file_path.stat().st_size,
                        "content_preview": content[:1000] + "..." if len(content) > 1000 else content,
                        "full_content": content,
                        "character_count": len(content),
                        "word_count": len(content.split())
                    })
                except Exception as e:
                    logger.error(f"Error reading file {filename}: {e}")
                    files_info.append({
                        "file_type": filename.split('_')[-1].replace('.txt', ''),
                        "filename": filename,
                        "error": str(e)
                    })
            else:
                file_type_name = filename.split('_')[-1].replace('.txt', '')
                files_info.append({
                    "file_type": file_type_name,
                    "filename": filename,
                    "exists": False,
                    "message": f"File {filename} not found"
                })
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len([f for f in files_info if 'error' not in f and f.get('exists', True)])} extracted text files",
            data={
                "document_id": document_id,
                "document_title": doc.title,
                "document_language": doc.language,
                "files": files_info,
                "extracted_text_directory": str(extracted_text_dir)
            },
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Debug extracted text error: {e}")
        return ApiResponse(
            success=False,
            message=str(e),
            data=None,
            errors=[{"field": None, "message": str(e)}]
        )
