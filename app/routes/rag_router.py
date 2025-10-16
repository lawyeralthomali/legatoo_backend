from fastapi import APIRouter, UploadFile, Form, HTTPException
from typing import Dict, Any

from app.services.nowledge.knowledge_service import process_upload as process_upload_nowledge
from app.services.nowledge.knowledge_service import answer_query as answer_query_nowledge
from app.schemas.response import ApiResponse, create_success_response, create_error_response

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/upload", response_model=ApiResponse)
async def upload_file(file: UploadFile) -> ApiResponse[Dict[str, Any]]:
    """
    Upload a file for RAG processing.
    
    **File Upload for RAG**:
    - Accepts various file formats (PDF, DOCX, TXT)
    - Processes and chunks the content
    - Stores in knowledge base for retrieval
    - Returns processing statistics
    
    **Response**:
    - Success: Processing statistics and chunk count
    - Error: Detailed error information
    """
    try:
        if not file.filename:
            return create_error_response(
                message="No file provided",
                errors=[{"field": "file", "message": "File is required"}]
            )
        
        chunks_count = await process_upload_nowledge(file)
        
        response_data = {
            "filename": file.filename,
            "chunks_created": chunks_count,
            "status": "processed"
        }
        
        return create_success_response(
            message=f"File '{file.filename}' processed successfully with {chunks_count} chunks",
            data=response_data
        )
        
    except Exception as e:
        return create_error_response(
            message=f"Failed to process file: {str(e)}"
        )


@router.post("/chat", response_model=ApiResponse)
async def chat(query: str = Form(...)) -> ApiResponse[Dict[str, Any]]:
    """
    Chat with the RAG system using uploaded documents.
    
    **RAG Chat**:
    - Queries the knowledge base for relevant information
    - Generates contextual responses based on uploaded documents
    - Provides source citations when available
    
    **Parameters**:
    - query: The question or query to ask
    
    **Response**:
    - Success: Answer with context and sources
    - Error: Query processing error information
    """
    try:
        if not query or len(query.strip()) < 3:
            return create_error_response(
                message="Invalid query",
                errors=[{"field": "query", "message": "Query must be at least 3 characters long"}]
            )
        
        answer = await answer_query_nowledge(query.strip())
        
        response_data = {
            "query": query.strip(),
            "answer": answer,
            "timestamp": "2025-01-16T17:00:00Z"  # You can add actual timestamp if needed
        }
        
        return create_success_response(
            message="Query processed successfully",
            data=response_data
        )
        
    except Exception as e:
        return create_error_response(
            message=f"Failed to process query: {str(e)}"
        )