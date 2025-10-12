import logging
import json
import re
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ...models.legal_knowledge import KnowledgeChunk
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG Service for Legal Laws - Simplified Document-Based Implementation
    
    Handles complete RAG pipeline:
    1. Law document ingestion from files (PDF/DOCX/TXT)
    2. Smart text chunking with context preservation  
    3. Embedding generation for semantic search
    4. Similarity-based retrieval with hybrid search
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize RAG Service.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.embedding_service = EmbeddingService(db)
        
        # Smart chunking settings
        self.max_chunk_words = 400
        self.min_chunk_words = 50
        self.chunk_overlap_words = 50
        
        # Search settings
        self.default_top_k = 5
        self.default_threshold = 0.6

    # ==================== DOCUMENT INGESTION ====================

    async def ingest_law_document(self, file_path: str, law_metadata: Dict) -> Dict:
        """
        Ingest law document directly from file with smart processing.
        
        Args:
            file_path: Path to document file (PDF/DOCX/TXT)
            law_metadata: Dictionary containing law metadata
            
        Returns:
            Dict with ingestion results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"📥 Starting law document ingestion: {law_metadata.get('law_name', 'Unknown')}")
            
            # 1. Read document file
            document_data = await self._read_document_file(file_path)
            logger.info(f"📄 Read document: {len(document_data['full_text'])} characters")
            
            # 2. Clean and preprocess text
            cleaned_text = self._clean_legal_text(document_data['full_text'])
            logger.info(f"🧹 Cleaned text: {len(cleaned_text)} characters")
            
            # 3. Smart chunking
            chunks = self._smart_chunking(cleaned_text, law_metadata)
            logger.info(f"✂️ Created {len(chunks)} chunks from document")
            
            if not chunks:
                return {
                    'success': False,
                    'error': 'No valid chunks created from document'
                }
            
            # 4. Store chunks with embeddings
            storage_result = await self._store_chunks_with_embeddings(chunks)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'success': True,
                'law_name': law_metadata.get('law_name'),
                'chunks_created': len(chunks),
                'chunks_stored': storage_result['chunks_stored'],
                'processing_time': round(processing_time, 2),
                'file_type': document_data['file_type'],
                'total_words': sum(chunk['word_count'] for chunk in chunks)
            }
            
        except Exception as e:
            logger.error(f"❌ Law document ingestion failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    async def _read_document_file(self, file_path: str) -> Dict:
        """Read document files of different types"""
        try:
            if file_path.endswith('.docx'):
                import docx
                doc = docx.Document(file_path)
                full_text = "\n".join([
                    paragraph.text for paragraph in doc.paragraphs 
                    if paragraph.text.strip()
                ])
                
            elif file_path.endswith('.pdf'):
                import PyPDF2
                full_text = ""
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n"
                            
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    full_text = file.read()
                    
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            return {
                'full_text': full_text,
                'file_type': file_path.split('.')[-1].upper()
            }
            
        except ImportError as e:
            logger.error(f"❌ Required library not installed: {e}")
            raise ImportError(f"Please install required library: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to read document: {e}")
            raise

    def _clean_legal_text(self, text: str) -> str:
        """Clean and normalize legal text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize Arabic text
        text = self.normalize_arabic_text(text)
        
        # Remove common document artifacts
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks
        text = re.sub(r'Page\s+\d+\s+', '', text)  # Remove page numbers
        text = re.sub(r'\x0c', '', text)  # Remove form feeds
        
        return text.strip()

    def _smart_chunking(self, text: str, law_metadata: Dict) -> List[Dict]:
        """Smart chunking that preserves legal context"""
        if not text.strip():
            return []
            
        chunks = []
        
        # Split into natural paragraphs
        paragraphs = self._split_into_paragraphs(text)
        logger.info(f"📝 Found {len(paragraphs)} paragraphs for chunking")
        
        current_chunk = ""
        current_word_count = 0
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
                
            para_words = len(paragraph.split())
            
            # Handle very long paragraphs by splitting them
            if para_words > self.max_chunk_words:
                # Save current chunk if exists
                if current_chunk and current_word_count >= self.min_chunk_words:
                    chunks.append(self._create_chunk(current_chunk, law_metadata))
                    current_chunk = ""
                    current_word_count = 0
                
                # Split the long paragraph
                sub_chunks = self._split_long_paragraph(paragraph)
                for sub_chunk in sub_chunks:
                    if len(sub_chunk.split()) >= self.min_chunk_words:
                        chunks.append(self._create_chunk(sub_chunk, law_metadata))
                continue
            
            # Check if adding this paragraph would exceed limit
            if current_word_count + para_words > self.max_chunk_words and current_chunk:
                # Save current chunk and start new one with smart overlap
                chunks.append(self._create_chunk(current_chunk, law_metadata))
                
                # Smart overlap: take last few sentences for context
                overlap = self._get_smart_overlap(current_chunk)
                current_chunk = overlap + "\n" + paragraph if overlap else paragraph
                current_word_count = len(overlap.split()) + para_words if overlap else para_words
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n" + paragraph
                else:
                    current_chunk = paragraph
                current_word_count += para_words
        
        # Add the final chunk if valid
        if current_chunk and current_word_count >= self.min_chunk_words:
            chunks.append(self._create_chunk(current_chunk, law_metadata))
        
        logger.info(f"✅ Created {len(chunks)} chunks with smart chunking")
        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into natural paragraphs"""
        # Split by multiple newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter and clean paragraphs
        cleaned_paragraphs = []
        for para in paragraphs:
            cleaned = para.strip()
            if cleaned and len(cleaned.split()) >= 3:  # Minimum 3 words
                cleaned_paragraphs.append(cleaned)
        
        return cleaned_paragraphs

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """Split a long paragraph into smaller chunks"""
        sentences = self._split_into_sentences(paragraph)
        chunks = []
        current_chunk = []
        current_words = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            if current_words + sentence_words > self.max_chunk_words and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                if len(chunk_text.split()) >= self.min_chunk_words:
                    chunks.append(chunk_text)
                
                # Start new chunk with last sentence for overlap
                current_chunk = [sentence] if sentence_words <= self.max_chunk_words else []
                current_words = sentence_words
            else:
                current_chunk.append(sentence)
                current_words += sentence_words
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text.split()) >= self.min_chunk_words:
                chunks.append(chunk_text)
        
        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences (Arabic-friendly)"""
        # Arabic sentence endings: . ? ! 。 ؟ !
        sentence_endings = r'[.؟!]\s+'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_smart_overlap(self, chunk_text: str) -> str:
        """Get smart overlap from previous chunk for context"""
        sentences = self._split_into_sentences(chunk_text)
        
        # Take last 1-2 sentences for overlap
        if len(sentences) >= 2:
            overlap_sentences = sentences[-2:]
        elif sentences:
            overlap_sentences = sentences[-1:]
        else:
            return ""
        
        overlap_text = ". ".join(overlap_sentences) + ("." if overlap_sentences else "")
        return overlap_text if len(overlap_text.split()) <= self.chunk_overlap_words else ""

    def _create_chunk(self, content: str, law_metadata: Dict) -> Dict:
        """Create chunk object with metadata"""
        word_count = len(content.split())
        
        return {
            'content': content.strip(),
            'word_count': word_count,
            'law_name': law_metadata.get('law_name', 'Unknown Law'),
            'law_type': law_metadata.get('law_type', 'law'),
            'jurisdiction': law_metadata.get('jurisdiction', 'السعودية'),
            'metadata': {
                'original_filename': law_metadata.get('original_filename'),
                'file_type': law_metadata.get('file_type'),
                'upload_time': datetime.utcnow().isoformat()
            }
        }

    async def _store_chunks_with_embeddings(self, chunks: List[Dict]) -> Dict:
        """Store chunks and generate embeddings"""
        start_time = datetime.utcnow()
        stored_count = 0
        failed_count = 0
        
        for i, chunk_data in enumerate(chunks):
            try:
                # Generate embedding
                embedding = await self.generate_embedding(chunk_data['content'])
                
                # Create and store chunk
                chunk = KnowledgeChunk(
                    content=chunk_data['content'],
                    embedding_vector=json.dumps(embedding),
                    tokens_count=chunk_data['word_count'],
                    law_source_id=None,  # Will be updated when we have document model
                    metadata=chunk_data.get('metadata', {})
                )
                
                self.db.add(chunk)
                stored_count += 1
                
                # Commit every 10 chunks to manage memory
                if stored_count % 10 == 0:
                    await self.db.commit()
                    logger.info(f"💾 Saved {stored_count} chunks so far...")
                    
            except Exception as e:
                logger.error(f"❌ Failed to store chunk {i}: {str(e)}")
                failed_count += 1
                continue
        
        # Final commit
        await self.db.commit()
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ Storage completed: {stored_count} successful, {failed_count} failed")
        
        return {
            'chunks_stored': stored_count,
            'chunks_failed': failed_count,
            'processing_time': processing_time
        }

    # ==================== EMBEDDING GENERATION ====================

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            normalized_text = self.normalize_arabic_text(text)
            embedding = self.embedding_service._encode_text(normalized_text)
            return embedding
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {str(e)}")
            raise

    # ==================== SEMANTIC SEARCH ====================

    async def search(
        self,
        query: str,
        top_k: int = None,
        threshold: float = None,
        law_source_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for relevant law chunks using hybrid semantic search.
        """
        start_time = datetime.utcnow()
        top_k = top_k or self.default_top_k
        threshold = threshold or self.default_threshold
        
        try:
            logger.info(f"🔍 RAG Search: '{query[:50]}...' (top_k={top_k}, threshold={threshold})")
            
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Get chunks with embeddings
            chunks = await self._get_chunks_with_embeddings(law_source_id)
            
            if not chunks:
                return self._create_empty_search_result(query, start_time)
            
            # Perform hybrid search
            results = await self._hybrid_search(query, query_embedding, chunks, top_k, threshold)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'success': True,
                'query': query,
                'total_results': len(results),
                'results': results,
                'processing_time': round(processing_time, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'total_results': 0,
                'results': [],
                'processing_time': 0.0
            }

    async def _get_chunks_with_embeddings(self, law_source_id: Optional[int] = None):
        """Get chunks with embeddings from database"""
        query_builder = (
            select(KnowledgeChunk)
            .where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != ''
                )
            )
        )
        
        if law_source_id:
            query_builder = query_builder.where(
                KnowledgeChunk.law_source_id == law_source_id
            )
        
        result = await self.db.execute(query_builder)
        return result.scalars().all()

    async def _hybrid_search(self, query: str, query_embedding: List[float], 
                           chunks: List, top_k: int, threshold: float) -> List[Dict]:
        """Perform hybrid semantic + lexical search"""
        if not chunks:
            return []
        
        # Prepare embeddings and references
        embeddings, chunk_refs = self._prepare_embeddings(chunks)
        
        if not embeddings:
            return []
        
        # Semantic similarity
        semantic_scores = self._calculate_semantic_similarity(query_embedding, embeddings)
        
        # Lexical similarity (for Arabic text)
        lexical_scores = self._calculate_lexical_similarity(query, chunk_refs)
        
        # Combine scores
        combined_scores = self._combine_scores(semantic_scores, lexical_scores)
        
        # Apply threshold and get top results
        results = self._get_top_results(combined_scores, chunk_refs, top_k, threshold)
        
        return results

    def _prepare_embeddings(self, chunks: List):
        """Prepare embeddings for similarity calculation"""
        embeddings = []
        chunk_refs = []
        
        for chunk in chunks:
            try:
                embedding_array = np.array(json.loads(chunk.embedding_vector), dtype=np.float32)
                embeddings.append(embedding_array)
                chunk_refs.append(chunk)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse embedding for chunk {chunk.id}: {e}")
                continue
        
        return embeddings, chunk_refs

    def _calculate_semantic_similarity(self, query_embedding: List[float], embeddings: List) -> np.ndarray:
        """Calculate semantic similarity using cosine similarity"""
        if not embeddings:
            return np.array([])
        
        # Convert to numpy arrays and normalize
        E = np.vstack(embeddings).astype(np.float32)
        E = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-12)
        
        q = np.array(query_embedding, dtype=np.float32)
        q = q / (np.linalg.norm(q) + 1e-12)
        
        # Cosine similarity
        return E @ q

    def _calculate_lexical_similarity(self, query: str, chunks: List) -> np.ndarray:
        """Calculate lexical similarity for Arabic text"""
        if not chunks:
            return np.array([])
        
        # Normalize query
        normalized_query = self.normalize_arabic_text(query)
        query_tokens = self._tokenize_arabic(normalized_query)
        
        if not query_tokens:
            return np.zeros(len(chunks))
        
        query_set = set(query_tokens)
        lexical_scores = np.zeros(len(chunks))
        
        for i, chunk in enumerate(chunks):
            try:
                chunk_tokens = self._tokenize_arabic(chunk.content)
                chunk_set = set(chunk_tokens)
                
                if not chunk_set:
                    continue
                
                # Jaccard similarity
                intersection = len(query_set & chunk_set)
                union = len(query_set | chunk_set)
                
                if union > 0:
                    lexical_scores[i] = intersection / union
            except Exception as e:
                logger.warning(f"⚠️ Failed to calculate lexical similarity for chunk {chunk.id}: {e}")
                continue
        
        return lexical_scores

    def _tokenize_arabic(self, text: str) -> List[str]:
        """Tokenize Arabic text"""
        normalized = self.normalize_arabic_text(text)
        # Remove punctuation and split
        cleaned = re.sub(r'[^\w\u0600-\u06FF\s]', ' ', normalized)
        tokens = [token for token in cleaned.split() if len(token) >= 2]
        return tokens

    def _combine_scores(self, semantic_scores: np.ndarray, lexical_scores: np.ndarray, 
                       semantic_weight: float = 0.85) -> np.ndarray:
        """Combine semantic and lexical scores"""
        if semantic_scores.size == 0:
            return lexical_scores
        if lexical_scores.size == 0:
            return semantic_scores
        
        return semantic_weight * semantic_scores + (1 - semantic_weight) * lexical_scores

    def _get_top_results(self, scores: np.ndarray, chunks: List, top_k: int, threshold: float) -> List[Dict]:
        """Get top results above threshold"""
        if scores.size == 0:
            return []
        
        # Get indices of scores above threshold
        above_threshold = np.where(scores >= threshold)[0]
        
        if above_threshold.size == 0:
            # If no results above threshold, get top N anyway
            top_indices = np.argpartition(scores, -top_k)[-top_k:]
        else:
            top_indices = above_threshold
        
        # Sort by score
        sorted_indices = top_indices[np.argsort(-scores[top_indices])]
        
        results = []
        for idx in sorted_indices[:top_k]:
            chunk = chunks[idx]
            score = float(scores[idx])
            
            results.append({
                'chunk_id': chunk.id,
                'content': chunk.content,
                'similarity_score': round(score, 4),
                'law_source_id': chunk.law_source_id,
                'law_source_name': getattr(chunk.law_source, 'name', None) if hasattr(chunk, 'law_source') else None,
                'word_count': chunk.tokens_count or len(chunk.content.split()),
                'metadata': chunk.metadata or {}
            })
        
        return results

    def _create_empty_search_result(self, query: str, start_time: datetime) -> Dict:
        """Create empty search result"""
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            'success': True,
            'query': query,
            'total_results': 0,
            'results': [],
            'processing_time': round(processing_time, 2)
        }

    # ==================== TEXT NORMALIZATION ====================

    def normalize_arabic_text(self, text: str) -> str:
        """
        Normalize Arabic text for better embedding quality.
        """
        if not text:
            return ""
        
        # Remove Arabic diacritics (tashkeel)
        arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
        text = arabic_diacritics.sub('', text)
        
        # Normalize Alif variants
        text = re.sub(r'[إأآا]', 'ا', text)
        
        # Normalize Ya variants
        text = re.sub(r'ى', 'ي', text)
        
        # Normalize Ta Marbuta
        text = re.sub(r'ة', 'ه', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    # ==================== UTILITY METHODS ====================

    async def get_system_status(self) -> Dict[str, Any]:
        """Get RAG system status"""
        try:
            from sqlalchemy import func
            
            # Get total chunks
            total_result = await self.db.execute(select(func.count(KnowledgeChunk.id)))
            total_chunks = total_result.scalar() or 0
            
            # Get chunks with embeddings
            with_embeddings_result = await self.db.execute(
                select(func.count(KnowledgeChunk.id)).where(
                    and_(
                        KnowledgeChunk.embedding_vector.isnot(None),
                        KnowledgeChunk.embedding_vector != ''
                    )
                )
            )
            chunks_with_embeddings = with_embeddings_result.scalar() or 0
            
            # Calculate coverage
            coverage = (chunks_with_embeddings / total_chunks * 100) if total_chunks > 0 else 0.0
            
            return {
                'status': 'operational',
                'total_chunks': total_chunks,
                'chunks_with_embeddings': chunks_with_embeddings,
                'embedding_coverage': round(coverage, 2),
                'chunking_settings': {
                    'max_chunk_words': self.max_chunk_words,
                    'min_chunk_words': self.min_chunk_words,
                    'chunk_overlap_words': self.chunk_overlap_words
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get system status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }