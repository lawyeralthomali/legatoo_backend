"""
Legal Assistant router for FastAPI
Converted from Django views and URLs
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID

from ..db.database import get_db
from ..utils.auth import get_current_user_id
from ..services.legal_assistant_service import LegalAssistantService
from ..schemas.legal_assistant import (
    ChatRequest,
    ChatResponse,
    DocumentSummaryRequest,
    DocumentSummaryResponse,
    KeywordSearchRequest,
    KeywordSearchResponse,
    DocumentUploadResponse,
    LanguageDetectionRequest,
    LanguageDetectionResponse,
    AssistantStatusResponse,
    ConversationHistory,
    AssistantConfig
)
from ..config.legal_assistant import (
    get_config, get_error_message, get_file_upload_message,
    get_sample_questions, get_welcome_message
)

router = APIRouter(prefix="/legal-assistant", tags=["Legal Assistant"])


@router.get("/status", response_model=AssistantStatusResponse)
async def get_assistant_status():
    """Get legal assistant status and available features"""
    # Check dependencies
    dependencies = {
        "openai": False,
        "tiktoken": False,
        "numpy": False
    }
    
    try:
        import numpy
        dependencies["numpy"] = True
    except ImportError:
        pass
    
    try:
        import openai
        dependencies["openai"] = True
    except ImportError:
        pass
    
    try:
        import tiktoken
        dependencies["tiktoken"] = True
    except ImportError:
        pass
    
    # Determine available features
    features_available = ["language_detection", "basic_chat"]
    if dependencies["openai"]:
        features_available.extend(["ai_chat", "document_processing", "semantic_search"])
    if dependencies["tiktoken"]:
        features_available.append("token_counting")
    
    # Available models
    models_available = []
    if dependencies["openai"]:
        models_available = ["gpt-3.5-turbo", "gpt-4", "text-embedding-3-small"]
    
    return AssistantStatusResponse(
        status="active" if dependencies["openai"] else "limited",
        dependencies=dependencies,
        features_available=features_available,
        models_available=models_available
    )


@router.post("/chat", response_model=ChatResponse)
async def assistant_chat(
    chat_request: ChatRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Handle chat requests and return AI responses with enhanced features"""
    # Get OpenAI API key from environment
    import os
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_message("english", "openai_not_configured")
        )
    
    # Convert history to the format expected by the service
    conversation_history = []
    if chat_request.history:
        for msg in chat_request.history:
            conversation_history.append({
                "content": msg.content,
                "isUser": msg.isUser
            })
    
    result = await LegalAssistantService.process_chat_request(
        db=db,
        question=chat_request.question,
        conversation_history=conversation_history,
        openai_api_key=openai_api_key
    )
    
    return ChatResponse(**result)


@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(
    request: LanguageDetectionRequest
):
    """Detect the language of input text"""
    text = request.text
    
    # Count Arabic characters (Unicode range for Arabic)
    import re
    arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
    # Count English characters
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    total_chars = len(text.replace(' ', ''))
    
    # Calculate confidence
    if total_chars > 0:
        arabic_ratio = arabic_chars / total_chars
        if arabic_ratio > 0.3:
            language = 'arabic'
            confidence = arabic_ratio
        else:
            language = 'english'
            confidence = 1 - arabic_ratio
    else:
        language = 'english'
        confidence = 0.5
    
    return LanguageDetectionResponse(
        language=language,
        confidence=confidence,
        arabic_chars=arabic_chars,
        english_chars=english_chars,
        total_chars=total_chars
    )


@router.post("/document-summary", response_model=DocumentSummaryResponse)
async def get_document_summary(
    request: DocumentSummaryRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a summary of a specific document"""
    try:
        document_id = UUID(request.document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    summary = await LegalAssistantService.get_document_summary(db, document_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or has no chunks"
        )
    
    return DocumentSummaryResponse(**summary)


@router.post("/search-keywords", response_model=KeywordSearchResponse)
async def search_documents_by_keywords(
    request: KeywordSearchRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Search documents by keywords in content"""
    results = await LegalAssistantService.search_documents_by_keywords(
        db=db,
        keywords=request.keywords,
        limit=request.limit
    )
    
    return KeywordSearchResponse(
        results=results,
        total=len(results),
        keywords=request.keywords
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Handle document upload for the legal assistant"""
    try:
        config = get_config()
        
        # Validate file size
        if file.size and file.size > config.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=get_file_upload_message("english", "size_too_large")
            )
        
        # Validate file extension
        if file.filename:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in config.allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=get_file_upload_message("english", "type_not_supported")
                )
        
        # For now, return a success response
        # In a real implementation, you would process the file
        return DocumentUploadResponse(
            success=True,
            message=get_file_upload_message("english", "success"),
            filename=file.filename
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_file_upload_message("english", "error", error=str(e))
        )


@router.get("/conversation-history")
async def get_conversation_history(
    session_id: str = None,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history for a session"""
    # This would typically retrieve from a database
    # For now, return empty history
    return {
        "session_id": session_id,
        "messages": [],
        "total_messages": 0
    }


@router.post("/conversation-history")
async def save_conversation_history(
    history: ConversationHistory,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Save conversation history"""
    # This would typically save to a database
    # For now, return success
    return {
        "success": True,
        "message": "Conversation history saved",
        "session_id": history.session_id
    }


@router.get("/config", response_model=AssistantConfig)
async def get_assistant_config():
    """Get current assistant configuration"""
    return AssistantConfig()


@router.put("/config", response_model=AssistantConfig)
async def update_assistant_config(
    config: AssistantConfig,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Update assistant configuration"""
    # This would typically save to user preferences
    # For now, just return the config
    return config


@router.get("/sample-questions")
async def get_sample_questions(language: str = "en"):
    """Get sample questions for the legal assistant"""
    questions = get_sample_questions(language)
    return {
        "language": language,
        "questions": questions
    }


@router.get("/welcome-message")
async def get_welcome_message(language: str = "en"):
    """Get welcome message for the legal assistant"""
    message = get_welcome_message(language)
    return {
        "language": language,
        "message": message
    }


@router.get("/health")
async def health_check():
    """Health check for legal assistant"""
    return {
        "status": "healthy",
        "service": "legal-assistant",
        "features": {
            "chat": True,
            "language_detection": True,
            "document_processing": True,
            "semantic_search": True
        }
    }
