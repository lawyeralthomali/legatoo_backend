"""
Legal Assistant service for FastAPI
Converted from Django views and RAG engine
"""
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession

# Optional imports - will be checked at runtime
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
from sqlalchemy import select, and_
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import HTTPException, status
from datetime import datetime

# Optional imports - will be checked at runtime
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from ..models.legal_document import LegalDocumentChunk, LegalDocument
from ..config.legal_assistant import (
    get_config, get_system_prompt, get_user_prompt_template, 
    get_error_message, ERROR_MESSAGES
)


class LegalAssistantService:
    """Service for handling legal assistant business logic"""
    
    @staticmethod
    def detect_language(text: str) -> str:
        """Detect if text is primarily Arabic or English"""
        # Count Arabic characters (Unicode range for Arabic)
        arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text))
        # Count English characters
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        # If Arabic characters are more than 30% of the text, consider it Arabic
        total_chars = len(text.replace(' ', ''))
        if total_chars > 0:
            arabic_ratio = arabic_chars / total_chars
            if arabic_ratio > 0.3:
                return 'arabic'
        
        return 'english'
    
    @staticmethod
    def get_embedding(text: str, openai_api_key: str) -> List[float]:
        """Generate embedding for given text using OpenAI API"""
        if not OPENAI_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI not installed. Please install: pip install openai"
            )
        
        client = OpenAI(api_key=openai_api_key)
        
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        
        return response.data[0].embedding
    
    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not NUMPY_AVAILABLE:
            # Fallback implementation without numpy
            if len(a) != len(b):
                return 0.0
            
            dot_product = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(x * x for x in b) ** 0.5
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        
        # Use numpy if available
        a = np.array(a)
        b = np.array(b)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0
        
        return dot_product / (norm_a * norm_b)
    
    @staticmethod
    def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
        """Count tokens in text using tiktoken"""
        if TIKTOKEN_AVAILABLE:
            try:
                encoding = tiktoken.encoding_for_model(model)
                return len(encoding.encode(text))
            except:
                pass
        
        # Fallback: rough estimation (1 token ≈ 4 characters)
        return len(text) // 4
    
    @staticmethod
    def truncate_text_to_tokens(text: str, max_tokens: int, model: str = "gpt-3.5-turbo") -> str:
        """Truncate text to fit within token limit"""
        if TIKTOKEN_AVAILABLE:
            try:
                encoding = tiktoken.encoding_for_model(model)
                tokens = encoding.encode(text)
                if len(tokens) <= max_tokens:
                    return text
                
                # Truncate to max_tokens and decode back
                truncated_tokens = tokens[:max_tokens]
                return encoding.decode(truncated_tokens)
            except:
                pass
        
        # Fallback: rough estimation
        estimated_tokens = len(text) // 4
        if estimated_tokens <= max_tokens:
            return text
        
        # Truncate by characters (rough approximation)
        max_chars = max_tokens * 4
        return text[:max_chars] + "..."
    
    @staticmethod
    async def retrieve_relevant_chunks(
        db: AsyncSession,
        question: str,
        openai_api_key: str,
        top_k: int = 5,
        max_context_tokens: int = 8000
    ) -> List[LegalDocumentChunk]:
        """Retrieve top-k most relevant chunks for a given question with enhanced filtering"""
        try:
            # Generate embedding for the question
            question_embedding = LegalAssistantService.get_embedding(question, openai_api_key)
            
            # Get all chunks with embeddings
            result = await db.execute(
                select(LegalDocumentChunk)
                .join(LegalDocument)
                .where(
                    and_(
                        LegalDocumentChunk.embedding.isnot(None),
                        LegalDocumentChunk.embedding != []
                    )
                )
            )
            chunks = result.scalars().all()
            
            if not chunks:
                return []
            
            # Calculate similarities with enhanced scoring
            similarities = []
            for chunk in chunks:
                if chunk.embedding and len(chunk.embedding) > 0:
                    similarity = LegalAssistantService.cosine_similarity(question_embedding, chunk.embedding)
                    
                    # Apply additional scoring factors
                    enhanced_score = similarity
                    
                    # Boost score for recent documents
                    if chunk.document.created_at:
                        days_old = (datetime.now() - chunk.document.created_at).days
                        if days_old < 365:  # Documents less than a year old
                            enhanced_score *= 1.1
                    
                    # Boost score for official documents
                    if chunk.document.title and any(keyword in chunk.document.title.lower() for keyword in ['قانون', 'نظام', 'لائحة', 'law', 'regulation', 'statute']):
                        enhanced_score *= 1.2
                    
                    # Boost score for longer, more detailed chunks
                    if len(chunk.content) > 200:
                        enhanced_score *= 1.05
                    
                    similarities.append((enhanced_score, similarity, chunk))
            
            # Sort by enhanced similarity score (descending)
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Select chunks while respecting token limit and diversity
            selected_chunks = []
            current_tokens = 0
            used_documents = set()
            
            for enhanced_score, original_similarity, chunk in similarities[:top_k * 2]:  # Get more candidates for diversity
                # Estimate tokens for this chunk
                chunk_text = f"Document: {chunk.document.title}\nArticle: {chunk.article_number or 'N/A'}\nContent: {chunk.content}"
                chunk_tokens = LegalAssistantService.count_tokens(chunk_text)
                
                # Check if adding this chunk would exceed token limit
                if current_tokens + chunk_tokens <= max_context_tokens:
                    # Check for diversity (don't add too many chunks from the same document)
                    if len(selected_chunks) < top_k and len([c for c in selected_chunks if c.document.id == chunk.document.id]) < 2:
                        selected_chunks.append(chunk)
                        current_tokens += chunk_tokens
                        used_documents.add(chunk.document.id)
                
                # Stop if we have enough chunks
                if len(selected_chunks) >= top_k:
                    break
            
            # Sort selected chunks by original similarity score for better context ordering
            selected_chunks.sort(key=lambda chunk: next(score for enhanced_score, original_similarity, c in similarities if c.id == chunk.id), reverse=True)
            
            return selected_chunks
            
        except Exception as e:
            print(f"Error in retrieve_relevant_chunks: {str(e)}")
            return []
    
    @staticmethod
    async def process_chat_request(
        db: AsyncSession,
        question: str,
        conversation_history: List[Dict[str, Any]],
        openai_api_key: str
    ) -> Dict[str, Any]:
        """Process chat request and return AI response with enhanced features"""
        if not OPENAI_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI not installed. Please install: pip install openai"
            )
        
        try:
            # Get configuration
            config = get_config()
            
            # Detect language of the question
            question_language = LegalAssistantService.detect_language(question)
            
            # Retrieve relevant chunks with token limit
            relevant_chunks = await LegalAssistantService.retrieve_relevant_chunks(
                db, question, openai_api_key, top_k=config.top_k, max_context_tokens=config.max_context_tokens
            )
            
            # Prepare context from chunks
            context_text = ""
            sources_used = []
            if relevant_chunks:
                context_parts = []
                for chunk in relevant_chunks:
                    chunk_text = f"Document: {chunk.document.title}\nArticle: {chunk.article_number or 'N/A'}\nContent: {chunk.content}"
                    context_parts.append(chunk_text)
                    sources_used.append(chunk.document.title)
                context_text = "\n\n".join(context_parts)
            else:
                context_text = get_error_message(question_language, "no_relevant_docs")
            
            # Prepare conversation context for memory
            conversation_context = ""
            if conversation_history and len(conversation_history) > 0:
                # Include last 3 exchanges for context
                recent_history = conversation_history[-6:]  # Last 3 Q&A pairs
                history_parts = []
                for msg in recent_history:
                    if msg.get('isUser'):
                        history_parts.append(f"User: {msg.get('content', '')}")
                    else:
                        history_parts.append(f"Assistant: {msg.get('content', '')}")
                conversation_context = "\n".join(history_parts)
            
            # Create language-specific prompts with enhanced instructions
            system_prompt = get_system_prompt(question_language)
            user_prompt = get_user_prompt_template(question_language).format(
                conversation_context=conversation_context,
                context_text=context_text,
                question=question
            )

            # Check total token count before sending to API
            total_tokens = LegalAssistantService.count_tokens(system_prompt + user_prompt)
            max_tokens = config.max_context_tokens + 4000  # Buffer for system prompt and response
            
            if total_tokens > max_tokens:
                # Truncate the context if it's too long
                if question_language == 'arabic':
                    available_tokens = max_tokens - LegalAssistantService.count_tokens(system_prompt + f"\n\nالسؤال الحالي: {question}\n\nيرجى تقديم إجابة مفيدة ودقيقة بناءً على السياق القانوني المقدم أعلاه.")
                else:
                    available_tokens = max_tokens - LegalAssistantService.count_tokens(system_prompt + f"\n\nCurrent question: {question}\n\nPlease provide a helpful and accurate answer based on the legal context provided above.")
                
                if available_tokens > 200:  # Ensure we have some space for context
                    # Truncate the context
                    context_text = LegalAssistantService.truncate_text_to_tokens(context_text, available_tokens - 200)
                    if question_language == 'arabic':
                        user_prompt = f"""المحادثة السابقة:
{conversation_context}

السياق من الوثائق القانونية:
{context_text}

السؤال الحالي: {question}

يرجى تقديم إجابة مفيدة ودقيقة بناءً على السياق القانوني المقدم أعلاه."""
                    else:
                        user_prompt = f"""Previous conversation:
{conversation_context}

Context from legal documents:
{context_text}

Current question: {question}

Please provide a helpful and accurate answer based on the legal context provided above."""
                else:
                    # If we can't fit even minimal context, just answer without context
                    if question_language == 'arabic':
                        user_prompt = f"""السؤال: {question}

يرجى تقديم إجابة قانونية عامة. ملاحظة: لم تتوفر معلومات سياقية محددة من الوثائق."""
                    else:
                        user_prompt = f"""Question: {question}

Please provide a general legal answer. Note: No specific document context was available."""

            # Call OpenAI GPT with enhanced parameters
            client = OpenAI(api_key=openai_api_key)
            
            try:
                response = client.chat.completions.create(
                    model=config.default_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    top_p=config.top_p,
                    frequency_penalty=config.frequency_penalty,
                    presence_penalty=config.presence_penalty
                )
                
                answer = response.choices[0].message.content
                
                # Assess response quality
                quality_score = LegalAssistantService.assess_response_quality(answer, relevant_chunks, question_language)
                
                return {
                    'answer': answer,
                    'chunks_used': len(relevant_chunks),
                    'tokens_used': total_tokens,
                    'language': question_language,
                    'quality_score': quality_score,
                    'sources': sources_used[:config.max_sources],
                    'has_context': len(relevant_chunks) > 0
                }
                
            except openai.BadRequestError as e:
                if "context_length_exceeded" in str(e):
                    # Try with a more conservative approach
                    simplified_prompt = get_user_prompt_template(question_language, simplified=True).format(question=question)
                    fallback_system_prompt = get_system_prompt(f"{question_language}_fallback")
                    
                    response = client.chat.completions.create(
                        model=config.fallback_model,
                        messages=[
                            {"role": "system", "content": fallback_system_prompt},
                            {"role": "user", "content": simplified_prompt}
                        ],
                        max_tokens=config.max_fallback_tokens,
                        temperature=config.temperature
                    )
                    
                    answer = response.choices[0].message.content
                    answer += f"\n\n{get_error_message(question_language, 'context_note')}"
                    
                    return {
                        'answer': answer,
                        'chunks_used': 0,
                        'tokens_used': LegalAssistantService.count_tokens(simplified_prompt),
                        'language': question_language,
                        'quality_score': 'medium',
                        'sources': [],
                        'has_context': False
                    }
                else:
                    raise e
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing chat request: {str(e)}"
            )
    
    @staticmethod
    def assess_response_quality(answer: str, relevant_chunks: List[LegalDocumentChunk], language: str) -> str:
        """Assess the quality of the AI response"""
        config = get_config()
        
        if len(relevant_chunks) > 0:
            # High quality if we have relevant document chunks
            return 'high'
        elif len(answer) > config.high_quality_threshold:
            # Medium quality if we have a substantial answer without specific context
            return 'medium'
        else:
            # Low quality for short or generic answers
            return 'low'
    
    @staticmethod
    async def get_document_summary(db: AsyncSession, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a summary of a specific document"""
        try:
            result = await db.execute(
                select(LegalDocumentChunk)
                .where(LegalDocumentChunk.document_id == document_id)
                .order_by(LegalDocumentChunk.chunk_index)
            )
            chunks = result.scalars().all()
            
            if not chunks:
                return None
            
            # Combine all chunks for summary
            full_text = "\n".join([chunk.content for chunk in chunks])
            
            # Truncate if too long
            if len(full_text) > 2000:
                full_text = full_text[:2000] + "..."
            
            return {
                'title': chunks[0].document.title,
                'summary': full_text,
                'chunk_count': len(chunks),
                'total_length': len(full_text)
            }
        except Exception as e:
            print(f"Error getting document summary: {str(e)}")
            return None
    
    @staticmethod
    async def search_documents_by_keywords(db: AsyncSession, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents by keywords in content"""
        try:
            # Create search query
            query_conditions = []
            for keyword in keywords:
                query_conditions.append(LegalDocumentChunk.content.ilike(f"%{keyword}%"))
            
            result = await db.execute(
                select(LegalDocumentChunk)
                .join(LegalDocument)
                .where(and_(*query_conditions))
                .limit(limit)
            )
            chunks = result.scalars().all()
            
            results = []
            for chunk in chunks:
                results.append({
                    'document_id': str(chunk.document.id),
                    'title': chunk.document.title,
                    'content_preview': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    'relevance_score': sum(1 for keyword in keywords if keyword.lower() in chunk.content.lower())
                })
            
            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results
            
        except Exception as e:
            print(f"Error in search_documents_by_keywords: {str(e)}")
            return []
