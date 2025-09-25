"""
Legal Document router for FastAPI
Converted from Django views and URLs
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ..db.database import get_db
from ..utils.auth import get_current_user_id, TokenData
from ..services.legal_document_service import LegalDocumentService
from ..schemas.legal_document import (
    LegalDocumentCreate,
    LegalDocumentUpdate,
    LegalDocumentResponse,
    LegalDocumentListResponse,
    DocumentUploadRequest,
    DocumentProcessResponse,
    DocumentSearchRequest,
    DocumentSearchResponse
)

router = APIRouter(prefix="/legal-documents", tags=["Legal Documents"])


@router.get("/", response_model=LegalDocumentListResponse)
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    document_type: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all legal documents with optional filtering"""
    documents = await LegalDocumentService.get_documents(
        db=db,
        skip=skip,
        limit=limit,
        document_type=document_type,
        language=language
    )
    
    return LegalDocumentListResponse(
        documents=documents,
        total=len(documents),
        page=skip // limit + 1,
        size=limit
    )


@router.post("/upload", response_model=LegalDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Query(..., min_length=1, max_length=255),
    document_type: str = Query("other"),
    language: str = Query("ar"),
    notes: Optional[str] = Query(None),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Upload a legal document"""
    try:
        # Upload file
        file_path = await LegalDocumentService.upload_document_file(file)
        
        # Create document data
        document_data = LegalDocumentCreate(
            title=title,
            document_type=document_type,
            language=language,
            notes=notes
        )
        
        # Create document record
        document = await LegalDocumentService.create_document(
            db=db,
            document_data=document_data,
            uploaded_by_id=current_user_id,
            file_path=file_path
        )
        
        return document
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/{document_id}", response_model=LegalDocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific legal document by ID"""
    document = await LegalDocumentService.get_document_by_id(db, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


@router.put("/{document_id}", response_model=LegalDocumentResponse)
async def update_document(
    document_id: UUID,
    document_data: LegalDocumentUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a legal document"""
    # Check if document exists and user has permission
    document = await LegalDocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user owns the document
    if document.uploaded_by_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own documents"
        )
    
    updated_document = await LegalDocumentService.update_document(
        db=db,
        document_id=document_id,
        document_data=document_data
    )
    
    return updated_document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a legal document"""
    # Check if document exists and user has permission
    document = await LegalDocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user owns the document
    if document.uploaded_by_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own documents"
        )
    
    success = await LegalDocumentService.delete_document(db, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.post("/{document_id}/process", response_model=DocumentProcessResponse)
async def process_document(
    document_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Process document and create chunks with embeddings"""
    # Check if document exists and user has permission
    document = await LegalDocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user owns the document
    if document.uploaded_by_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only process your own documents"
        )
    
    # Get OpenAI API key from environment (you'll need to configure this)
    import os
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured"
        )
    
    result = await LegalDocumentService.process_document(
        db=db,
        document_id=document_id,
        openai_api_key=openai_api_key
    )
    
    return result


@router.get("/{document_id}/chunks")
async def get_document_chunks(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get chunks for a specific document"""
    document = await LegalDocumentService.get_document_by_id(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "document_id": str(document_id),
        "document_title": document.title,
        "chunks": document.chunks,
        "total_chunks": len(document.chunks)
    }


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    search_request: DocumentSearchRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Search documents using semantic search"""
    # Get OpenAI API key from environment
    import os
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not configured"
        )
    
    results = await LegalDocumentService.search_documents(
        db=db,
        search_request=search_request,
        openai_api_key=openai_api_key
    )
    
    return DocumentSearchResponse(
        results=results,
        total=len(results),
        query=search_request.query
    )


@router.get("/my-documents", response_model=LegalDocumentListResponse)
async def get_my_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's documents"""
    # This would need to be implemented in the service
    # For now, we'll use the general get_documents method
    documents = await LegalDocumentService.get_documents(
        db=db,
        skip=skip,
        limit=limit
    )
    
    # Filter by current user
    user_documents = [doc for doc in documents if doc.uploaded_by_id == current_user_id]
    
    return LegalDocumentListResponse(
        documents=user_documents,
        total=len(user_documents),
        page=skip // limit + 1,
        size=limit
    )
