"""
Legal Assistant router for FastAPI
Minimized version with only essential routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Union
from uuid import UUID

from ..db.database import get_db
from ..utils.auth import get_current_user_id
from ..services.legal_assistant_service import LegalAssistantService
from ..schemas.legal_assistant import (
    ChatRequest,
    ChatResponse,
    LanguageDetectionRequest,
    LanguageDetectionResponse,
    AssistantStatusResponse
)
from ..config.legal_assistant import get_error_message

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
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
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









