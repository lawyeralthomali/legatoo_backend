"""
RAG Service for law document processing and semantic search.
Simplified for production use with essential methods only.
"""

import logging
import json
import re
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete

from ...models.documnets import LawDocument, LawChunk
from .embedding_service import EmbeddingService
from ...config.embedding_config import EmbeddingConfig

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
MIN_CHUNK_SIZE = 100
MIN_PARAGRAPH_SIZE = 20
DEFAULT_BATCH_SIZE = 16
DEFAULT_THRESHOLD = 0.7
MAX_CONTEXT_LENGTH = 2000


class RAGService:
    """RAG service for legal document ingestion, chunking, embedding, and search."""
    
    def __init__(self, db: AsyncSession, model_name: Optional[str] = None):
        """Initialize RAG service with database session and embedding model."""
        self.db = db
        self.embedding_service = EmbeddingService(
            db, 
            model_name=model_name or EmbeddingConfig.get_default_model()
        )
        self.chunk_size = DEFAULT_CHUNK_SIZE
        self.chunk_overlap = DEFAULT_CHUNK_OVERLAP
        self.min_chunk_size = MIN_CHUNK_SIZE
        
        logger.info(f"RAG Service initialized: model={self.embedding_service.model_name}")
    
    # === Internal Helpers ===
    
    def _clean_arabic_text(self, text: str) -> str:
        """Clean Arabic text by removing extra whitespace and invalid characters."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\u0600-\u06FF\s\.\?\!،؛]', ' ', text)
        return text.strip()
    
    def _find_sentence_boundary(self, words: List[str], window: int = 10) -> Optional[int]:
        """Find natural sentence boundary in word list."""
        endings = ('.', '۔', '؟', '!', '،')
        for j in range(len(words) - 1, max(0, len(words) - window) - 1, -1):
            if any(words[j].endswith(end) for end in endings):
                return j + 1
        return None
    
    def _smart_chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into smart chunks optimized for Arabic legal documents."""
        if not text or not text.strip():
            return []
        
        text = self._clean_arabic_text(text)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        chunks = []
        chunk_idx = 0
        
        for para in paragraphs:
            words = para.split()
            
            if len(words) < MIN_PARAGRAPH_SIZE:
                continue
            
            # Short/medium paragraphs: add as-is
            if len(words) <= self.chunk_size:
                chunks.append({
                    'content': para,
                    'word_count': len(words),
                    'chunk_index': chunk_idx
                })
                chunk_idx += 1
                continue
            
            # Long paragraphs: split at sentence boundaries
            i = 0
            while i < len(words):
                end_idx = min(i + self.chunk_size, len(words))
                chunk_words = words[i:end_idx]
                
                # Find natural break
                if end_idx < len(words):
                    boundary = self._find_sentence_boundary(chunk_words)
                    if boundary:
                        chunk_words = chunk_words[:boundary]
                
                # Add if substantial
                if len(chunk_words) >= self.min_chunk_size // 2:
                    chunks.append({
                        'content': ' '.join(chunk_words),
                        'word_count': len(chunk_words),
                        'chunk_index': chunk_idx
                    })
                    chunk_idx += 1
                
                i += len(chunk_words) - self.chunk_overlap
        
        return chunks
    
    async def _read_document_file(self, file_path: str) -> Dict:
        """Read document file (PDF/DOCX/TXT) and return text with metadata."""
        file_size = os.path.getsize(file_path)
        file_ext = file_path.split('.')[-1].lower()
        
        if file_ext == 'docx':
            try:
                import docx
                doc = docx.Document(file_path)
                full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except ImportError:
                raise ImportError("Install python-docx: pip install python-docx")
                
        elif file_ext == 'pdf':
            try:
                import PyPDF2
                full_text = ""
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n"
            except ImportError:
                raise ImportError("Install PyPDF2: pip install PyPDF2")
                        
        elif file_ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        return {
            'full_text': full_text,
            'file_type': file_ext.upper(),
            'file_size': file_size
        }
    
    # === Core Public Methods ===
    
    async def process_document(
        self,
        document_id: int,
        text: str,
        generate_embeddings: bool = True
    ) -> Dict[str, Any]:
        """Process document: chunk text and optionally generate embeddings."""
        document = None
        
        try:
            # Get document
            result = await self.db.execute(
                select(LawDocument).where(LawDocument.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                return {'success': False, 'error': f"Document {document_id} not found"}
            
            # Update status
            document.status = 'processing'
            await self.db.commit()
            
            # Chunk text
            chunks_data = self._smart_chunk_text(text)
            
            if not chunks_data:
                return {'success': False, 'error': "No valid chunks created"}
            
            # Update metadata and delete old chunks
            document.total_chunks = len(chunks_data)
            document.processed_chunks = 0
            await self.db.execute(delete(LawChunk).where(LawChunk.document_id == document_id))
            
            # Create new chunks
            for chunk_data in chunks_data:
                self.db.add(LawChunk(
                    document_id=document_id,
                    content=chunk_data['content'],
                    word_count=chunk_data['word_count'],
                    chunk_index=chunk_data['chunk_index'],
                    is_processed=False
                ))
            
            await self.db.commit()
            logger.info(f"Created {len(chunks_data)} chunks for document {document_id}")
            
            # Generate embeddings if requested
            if generate_embeddings:
                await self.generate_embeddings_for_document(document_id)
            
            # Update status
            document.status = 'completed' if generate_embeddings else 'chunked'
            document.processed_at = datetime.utcnow()
            await self.db.commit()
            
            return {
                'success': True,
                'document_id': document_id,
                'total_chunks': len(chunks_data),
                'embeddings_generated': generate_embeddings,
                'status': document.status
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            if document:
                document.status = 'failed'
                document.error_message = str(e)
                await self.db.commit()
            return {'success': False, 'error': str(e)}
    
    async def generate_embeddings_for_document(
        self,
        document_id: int,
        batch_size: int = DEFAULT_BATCH_SIZE
    ) -> Dict[str, Any]:
        """Generate embeddings for all unprocessed chunks of a document."""
        try:
            # Get document
            result = await self.db.execute(
                select(LawDocument).where(LawDocument.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                return {'success': False, 'error': f"Document {document_id} not found"}
            
            # Get unprocessed chunks
            chunks_result = await self.db.execute(
                select(LawChunk)
                .where(and_(
                    LawChunk.document_id == document_id,
                    LawChunk.is_processed == False
                ))
                .order_by(LawChunk.chunk_index)
            )
            chunks = chunks_result.scalars().all()
            
            if not chunks:
                return {'success': True, 'processed': 0, 'failed': 0, 'total': 0}
            
            # Initialize embedding service
            await self.embedding_service.initialize()
            
            # Process in batches
            processed = 0
            failed = 0
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                texts = [c.content for c in batch]
                
                try:
                    embeddings = await self.embedding_service.generate_batch_embeddings(texts)
                    
                    for chunk, embedding in zip(batch, embeddings):
                        # Handle list or ndarray
                        emb_json = json.dumps(embedding if isinstance(embedding, list) else embedding.tolist())
                        chunk.embedding_vector = emb_json
                        chunk.is_processed = True
                        processed += 1
                    
                    document.processed_chunks = processed
                    await self.db.commit()
                    
                except Exception as e:
                    logger.error(f"Batch processing failed: {e}")
                    failed += len(batch)
            
            # Final update
            document.status = 'completed' if failed == 0 else 'partially_completed'
            document.processed_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info(f"Embeddings done: {processed} success, {failed} failed")
            
            return {
                'success': True,
                'document_id': document_id,
                'processed': processed,
                'failed': failed,
                'total': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = DEFAULT_THRESHOLD,
        document_id: Optional[int] = None,
        jurisdiction: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across law chunks."""
        try:
            # Initialize and generate query embedding
            await self.embedding_service.initialize()
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Build query
            query_builder = (
                select(LawChunk, LawDocument)
                .join(LawDocument, LawChunk.document_id == LawDocument.id)
                .where(and_(
                    LawChunk.embedding_vector.isnot(None),
                    LawChunk.embedding_vector != '',
                    LawChunk.is_processed == True
                ))
            )
            
            # Apply filters
            if document_id:
                query_builder = query_builder.where(LawChunk.document_id == document_id)
            if jurisdiction:
                query_builder = query_builder.where(LawDocument.jurisdiction.ilike(f"%{jurisdiction}%"))
            
            # Execute
            result = await self.db.execute(query_builder)
            rows = result.all()
            
            # Calculate similarities
            results = []
            for chunk, doc in rows:
                try:
                    chunk_emb = json.loads(chunk.embedding_vector)
                    similarity = self.embedding_service.calculate_similarity(query_embedding, chunk_emb)
                    
                    if similarity >= threshold:
                        results.append({
                            'chunk_id': chunk.id,
                            'document_id': doc.id,
                            'document_name': doc.name,
                            'jurisdiction': doc.jurisdiction,
                            'content': chunk.content,
                            'similarity': float(similarity),
                            'chunk_index': chunk.chunk_index,
                            'word_count': chunk.word_count
                        })
                except Exception:
                    continue
            
            # Sort and limit
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def get_context_for_query(
        self,
        query: str,
        top_k: int = 5,
        max_length: int = MAX_CONTEXT_LENGTH
    ) -> str:
        """Get relevant context for RAG/AI analysis."""
        results = await self.semantic_search(query, top_k=top_k, threshold=0.6)
        
        if not results:
            return ""
        
        parts = []
        total_words = 0
        
        for r in results:
            words = len(r['content'].split())
            if total_words + words > max_length:
                break
            parts.append(f"[Source: {r['document_name']}]\n{r['content']}")
            total_words += words
        
        return "\n\n---\n\n".join(parts)
    
    async def ingest_law_document(self, file_path: str, law_metadata: Dict) -> Dict:
        """Ingest law document from file: read, chunk, embed, and store."""
        try:
            law_name = law_metadata.get('law_name', 'Unnamed')
            
            # Read file
            doc_data = await self._read_document_file(file_path)
            
            # Create document
            law_doc = LawDocument(
                name=law_name,
                type=law_metadata.get('law_type', 'law'),
                jurisdiction=law_metadata.get('jurisdiction', 'السعودية'),
                original_filename=law_metadata.get('original_filename', os.path.basename(file_path)),
                file_size=doc_data['file_size'],
                status='processing'
            )
            self.db.add(law_doc)
            await self.db.commit()
            await self.db.refresh(law_doc)
            
            # Process document
            result = await self.process_document(
                law_doc.id,
                doc_data['full_text'],
                generate_embeddings=True
            )
            
            if result['success']:
                # Get statistics
                chunks_result = await self.db.execute(
                    select(LawChunk).where(LawChunk.document_id == law_doc.id)
                )
                chunks = chunks_result.scalars().all()
                total_words = sum(c.word_count or 0 for c in chunks)
                
                return {
                    'success': True,
                    'law_name': law_name,
                    'chunks_created': result['total_chunks'],
                    'chunks_stored': result['total_chunks'],
                    'processing_time': 0.0,
                    'file_type': doc_data['file_type'],
                    'total_words': total_words,
                    'document_id': law_doc.id
                }
            else:
                law_doc.status = 'failed'
                law_doc.error_message = result.get('error', 'Unknown')
                await self.db.commit()
                return {'success': False, 'error': result.get('error')}
                
        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.6,
        law_source_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """API-compatible semantic search with formatted response."""
        start = datetime.utcnow()
        
        try:
            results = await self.semantic_search(query, top_k, threshold, document_id=law_source_id)
            duration = (datetime.utcnow() - start).total_seconds()
            
            # Format for API
            formatted = [{
                'chunk_id': r['chunk_id'],
                'content': r['content'],
                'similarity_score': round(r['similarity'], 4),
                'law_source_id': r['document_id'],
                'law_source_name': r['document_name'],
                'word_count': r['word_count'],
                'metadata': {
                    'jurisdiction': r.get('jurisdiction', ''),
                    'chunk_index': r.get('chunk_index', 0)
                }
            } for r in results]
            
            return {
                'success': True,
                'query': query,
                'total_results': len(formatted),
                'results': formatted,
                'processing_time': round(duration, 2)
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                'success': False,
                'query': query,
                'total_results': 0,
                'results': [],
                'processing_time': 0.0,
                'error': str(e)
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get RAG service statistics."""
        try:
            # Counts
            total_docs = (await self.db.execute(select(func.count(LawDocument.id)))).scalar() or 0
            total_chunks = (await self.db.execute(select(func.count(LawChunk.id)))).scalar() or 0
            chunks_with_emb = (await self.db.execute(
                select(func.count(LawChunk.id)).where(and_(
                    LawChunk.embedding_vector.isnot(None),
                    LawChunk.embedding_vector != '',
                    LawChunk.is_processed == True
                ))
            )).scalar() or 0
            
            # Status breakdown
            status_result = await self.db.execute(
                select(LawDocument.status, func.count(LawDocument.id)).group_by(LawDocument.status)
            )
            status_breakdown = {s: c for s, c in status_result}
            
            coverage = f"{(chunks_with_emb / total_chunks * 100):.1f}%" if total_chunks > 0 else "0%"
            
            return {
                'total_documents': total_docs,
                'total_chunks': total_chunks,
                'chunks_with_embeddings': chunks_with_emb,
                'embedding_coverage': coverage,
                'documents_by_status': status_breakdown,
                'model': self.embedding_service.model_name
            }
            
        except Exception as e:
            logger.error(f"Statistics failed: {e}")
            return {'error': str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status for health checks."""
        try:
            stats = await self.get_statistics()
            
            if 'error' in stats:
                return {'status': 'error', 'error': stats['error']}
            
            total = stats.get('total_chunks', 0)
            with_emb = stats.get('chunks_with_embeddings', 0)
            coverage = (with_emb / total * 100) if total > 0 else 0
            
            return {
                'status': 'operational',
                'total_documents': stats.get('total_documents', 0),
                'total_chunks': total,
                'chunks_with_embeddings': with_emb,
                'embedding_coverage': round(coverage, 2),
                'documents_by_status': stats.get('documents_by_status', {}),
                'chunking_settings': {
                    'max_chunk_words': self.chunk_size,
                    'min_chunk_words': self.min_chunk_size,
                    'chunk_overlap_words': self.chunk_overlap
                },
                'model': stats.get('model', 'unknown'),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {'status': 'error', 'error': str(e)}
