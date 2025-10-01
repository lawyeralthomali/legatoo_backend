"""
Legal Document service for FastAPI
Converted from Django views
"""
import os
import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status, UploadFile
# Optional imports - will be checked at runtime
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from ..models.legal_document import LegalDocument, LegalDocumentChunk
from ..schemas.legal_document import (
    LegalDocumentCreate, 
    LegalDocumentUpdate,
    DocumentUploadRequest,
    DocumentProcessResponse,
    DocumentSearchRequest
)


class LegalDocumentService:
    """Service for handling legal document business logic"""
    
    @staticmethod
    async def get_documents(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        document_type: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[LegalDocument]:
        """Get all legal documents with optional filtering"""
        query = select(LegalDocument).options(selectinload(LegalDocument.chunks))
        
        if document_type:
            query = query.where(LegalDocument.document_type == document_type)
        if language:
            query = query.where(LegalDocument.language == language)
        
        query = query.offset(skip).limit(limit).order_by(LegalDocument.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_document_by_id(db: AsyncSession, document_id: UUID) -> Optional[LegalDocument]:
        """Get a legal document by ID"""
        result = await db.execute(
            select(LegalDocument)
            .options(selectinload(LegalDocument.chunks))
            .where(LegalDocument.id == document_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_document(
        db: AsyncSession, 
        document_data: LegalDocumentCreate,
        uploaded_by_id: Optional[UUID],
        file_path: str
    ) -> LegalDocument:
        """Create a new legal document"""
        document = LegalDocument(
            title=document_data.title,
            file_path=file_path,
            uploaded_by_id=uploaded_by_id,
            document_type=document_data.document_type.value,
            language=document_data.language.value,
            notes=document_data.notes
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document
    
    @staticmethod
    async def update_document(
        db: AsyncSession, 
        document_id: UUID, 
        document_data: LegalDocumentUpdate
    ) -> Optional[LegalDocument]:
        """Update a legal document"""
        document = await LegalDocumentService.get_document_by_id(db, document_id)
        if not document:
            return None
        
        update_data = document_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(document, field):
                setattr(document, field, value.value if hasattr(value, 'value') else value)
        
        await db.commit()
        await db.refresh(document)
        return document
    
    @staticmethod
    async def delete_document(db: AsyncSession, document_id: UUID) -> bool:
        """Delete a legal document"""
        document = await LegalDocumentService.get_document_by_id(db, document_id)
        if not document:
            return False
        
        # Delete the file from filesystem
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception:
            pass  # Continue even if file deletion fails
        
        await db.delete(document)
        await db.commit()
        return True
    
    @staticmethod
    async def upload_document_file(
        file: UploadFile,
        upload_dir: str = "uploads/legal_documents"
    ) -> str:
        """Upload document file and return file path"""
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF, DOC, DOCX, and TXT files are allowed"
            )
        
        # Validate file size (max 10MB)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 10MB"
            )
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_name = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, file_name)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path
    
    @staticmethod
    def split_text_into_chunks(text: str, max_words: int = 800) -> List[str]:
        """Split text into chunks while preserving complete sentences"""
        # Split text into sentences (basic approach)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # If adding this sentence would exceed the limit, start a new chunk
            if current_word_count + sentence_words > max_words and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_word_count = sentence_words
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    @staticmethod
    def detect_article_numbers(text: str) -> Optional[str]:
        """Detect article numbers in Arabic text"""
        # Pattern to match Arabic article numbers like "المادة 3" or "المادة الثالثة"
        article_pattern = r'المادة\s+(\d+|[أ-ي]+)'
        matches = re.findall(article_pattern, text)
        return matches[0] if matches else None
    
    @staticmethod
    async def process_document(
        db: AsyncSession, 
        document_id: UUID,
        openai_api_key: str
    ) -> DocumentProcessResponse:
        """Process document and create chunks with embeddings"""
        document = await LegalDocumentService.get_document_by_id(db, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if required dependencies are available
        if not PYMUPDF_AVAILABLE:
            return DocumentProcessResponse(
                success=False,
                message="PyMuPDF not installed. Please install: pip install PyMuPDF",
                error="PyMuPDF dependency missing"
            )
        
        if not OPENAI_AVAILABLE:
            return DocumentProcessResponse(
                success=False,
                message="OpenAI not installed. Please install: pip install openai",
                error="OpenAI dependency missing"
            )
        
        try:
            # Update processing status
            document.processing_status = "processing"
            await db.commit()
            
            # Create OpenAI client
            client = OpenAI(api_key=openai_api_key)
            
            # Read PDF using PyMuPDF
            doc = fitz.open(document.file_path)
            full_text = ""
            
            # Extract text from all pages
            for page in doc:
                full_text += page.get_text()
            
            doc.close()
            
            # Split text into chunks
            chunks = LegalDocumentService.split_text_into_chunks(full_text, max_words=800)
            
            # Clear existing chunks for this document
            await db.execute(
                delete(LegalDocumentChunk).where(LegalDocumentChunk.document_id == document_id)
            )
            
            # Process each chunk
            for i, chunk_content in enumerate(chunks):
                # Detect article numbers
                article_number = LegalDocumentService.detect_article_numbers(chunk_content)
                
                # Generate embedding using OpenAI
                response = client.embeddings.create(
                    input=chunk_content,
                    model="text-embedding-3-small"
                )
                embedding = response.data[0].embedding
                
                # Create chunk record
                chunk = LegalDocumentChunk(
                    document_id=document_id,
                    chunk_index=i + 1,
                    content=chunk_content,
                    article_number=article_number,
                    embedding=embedding
                )
                db.add(chunk)
            
            # Mark as processed
            document.is_processed = True
            document.processing_status = "done"
            await db.commit()
            
            return DocumentProcessResponse(
                success=True,
                message="Document processed successfully",
                chunks_count=len(chunks)
            )
            
        except Exception as e:
            document.processing_status = "error"
            await db.commit()
            return DocumentProcessResponse(
                success=False,
                message="Error processing document",
                error=str(e)
            )
    
    @staticmethod
    async def search_documents(
        db: AsyncSession,
        search_request: DocumentSearchRequest,
        openai_api_key: str
    ) -> List[Dict[str, Any]]:
        """Search documents using semantic search"""
        # Check if OpenAI is available
        if not OPENAI_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI not installed. Please install: pip install openai"
            )
        
        try:
            # Create OpenAI client
            client = OpenAI(api_key=openai_api_key)
            
            # Generate embedding for search query
            response = client.embeddings.create(
                input=search_request.query,
                model="text-embedding-3-small"
            )
            query_embedding = response.data[0].embedding
            
            # Get all chunks with embeddings
            query = select(LegalDocumentChunk).where(
                LegalDocumentChunk.embedding.isnot(None)
            )
            
            if search_request.document_type:
                query = query.join(LegalDocument).where(
                    LegalDocument.document_type == search_request.document_type.value
                )
            
            if search_request.language:
                query = query.join(LegalDocument).where(
                    LegalDocument.language == search_request.language.value
                )
            
            result = await db.execute(query)
            chunks = result.scalars().all()
            
            # Calculate similarity scores (cosine similarity)
            results = []
            for chunk in chunks:
                if chunk.embedding:
                    # Calculate cosine similarity
                    similarity = LegalDocumentService.cosine_similarity(
                        query_embedding, chunk.embedding
                    )
                    
                    results.append({
                        "chunk_id": str(chunk.id),
                        "document_id": str(chunk.document_id),
                        "content": chunk.content,
                        "article_number": chunk.article_number,
                        "section_title": chunk.section_title,
                        "similarity": similarity
                    })
            
            # Sort by similarity and limit results
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:search_request.limit]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search error: {str(e)}"
            )
    
    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0
        
        return dot_product / (magnitude_a * magnitude_b)
