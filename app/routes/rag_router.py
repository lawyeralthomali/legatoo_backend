from fastapi import APIRouter, UploadFile, Form, HTTPException
from typing import Dict, Any

from app.services.knowledge.knowledge_service import process_upload 
from app.services.knowledge.knowledge_service import answer_query 
from app.schemas.response import ApiResponse, create_success_response, create_error_response

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

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
        
        chunks_count = await process_upload(file)
        
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
    - Provides source citations and retrieved context
    
    **Parameters**:
    - query: The question or query to ask
    
    **Response**:
    - Success: Answer with retrieved context including:
      - answer: The generated response
      - query: The original query
      - retrieved_context: Array of relevant legal articles with metadata
    - Error: Query processing error information
    """
    try:
        if not query or len(query.strip()) < 3:
            return create_error_response(
                message="Invalid query",
                errors=[{"field": "query", "message": "Query must be at least 3 characters long"}]
            )
        
        result = await answer_query(query.strip())
        
        # Handle both string and dictionary responses
        if isinstance(result, str):
            # Fallback for old format
            answer = result
            retrieved_context = []
        elif isinstance(result, dict):
            answer = result.get("answer", "❌ لم يتم العثور على إجابة مناسبة في قاعدة البيانات القانونية.")
            retrieved_context = result.get("retrieved_context", [])
        else:
            answer = "❌ لم يتم العثور على إجابة مناسبة في قاعدة البيانات القانونية."
            retrieved_context = []
        
        return create_success_response(
            message=answer,
            data={
                "answer": answer,
                "query": query.strip(),
                "retrieved_context": retrieved_context
            }
        )
        
    except Exception as e:
        return create_error_response(
            message=f"Failed to process query: {str(e)}"
        )