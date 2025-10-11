"""
Embedding Service - خدمة متكاملة لتوليد وإدارة embeddings للنصوص القانونية العربية

This service handles:
- Generating embeddings for legal text chunks using multilingual models
- Storing embeddings in the database
- Finding similar chunks using cosine similarity
- Batch processing for large datasets
"""

import logging
import json
import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sentence_transformers import SentenceTransformer
import torch

from ..models.legal_knowledge import KnowledgeChunk, KnowledgeDocument
from ..repositories.legal_knowledge_repository import KnowledgeChunkRepository

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    خدمة متكاملة لتوليد وإدارة الـ embeddings للنصوص القانونية العربية.
    
    Features:
    - Support for Arabic legal texts
    - Batch processing for efficiency
    - Similarity search with threshold
    - Caching for repeated queries
    - Error handling and retry logic
    """
    
    # Model configurations
    MODELS = {
        'default': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        'large': 'intfloat/multilingual-e5-large',
        'small': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        'arabic': 'Ezzaldin-97/STS-Arabert',
    }
    
    def __init__(self, db: AsyncSession, model_name: str = 'default'):
        """
        Initialize the embedding service.
        
        Args:
            db: Async database session
            model_name: Name of the model to use ('default', 'large', or 'small')
        """
        self.db = db
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.chunk_repo = KnowledgeChunkRepository(db)
        
        # Performance settings
        self.batch_size = 32
        self.max_seq_length = 512
        
        # Cache for embeddings (in-memory cache for frequent queries)
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_max_size = 1000
    
    def initialize_model(self) -> None:
        """
        تهيئة نموذج الـ embeddings المناسب للنصوص العربية القانونية.
        
        Uses sentence-transformers with multilingual support.
        Optimized for Arabic legal text understanding.
        
        Raises:
            RuntimeError: If model fails to load
        """
        try:
            model_path = self.MODELS.get(self.model_name, self.MODELS['default'])
            
            logger.info(f"🚀 Initializing embedding model: {model_path}")
            logger.info(f"📱 Using device: {self.device}")
            
            self.model = SentenceTransformer(model_path)
            self.model.to(self.device)
            
            # Set max sequence length
            self.model.max_seq_length = self.max_seq_length
            
            logger.info(f"✅ Model initialized successfully")
            logger.info(f"   Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding model: {str(e)}")
            raise RuntimeError(f"Failed to initialize embedding model: {str(e)}")
    
    def _ensure_model_loaded(self) -> None:
        """Ensure model is loaded before use."""
        if self.model is None:
            self.initialize_model()
    
    def _truncate_text(self, text: str, max_tokens: int = 512) -> str:
        """
        Truncate text to fit within model's max sequence length.
        
        Args:
            text: Input text
            max_tokens: Maximum number of tokens
            
        Returns:
            Truncated text
        """
        # Simple truncation by character count (approximate)
        # For more accurate truncation, use tokenizer
        max_chars = max_tokens * 4  # Approximate: 1 token ≈ 4 chars
        if len(text) > max_chars:
            logger.warning(f"⚠️ Truncating text from {len(text)} to {max_chars} characters")
            return text[:max_chars]
        return text
    
    def _encode_text(self, text: str) -> List[float]:
        """
        Encode a single text into embedding vector.
        - Normalizes text for caching key
        - Truncates to safe length
        - Uses normalize_embeddings=True for cosine-friendly vectors
        """
        self._ensure_model_loaded()

        # Lightweight normalization for cache key (no heavy Arabic normalization here)
        key = re.sub(r'\s+', ' ', (text or '').strip())

        # Cache first
        if key in self._embedding_cache:
            logger.debug("📦 Using cached embedding")
            return self._embedding_cache[key]

        # Truncate if necessary
        text = self._truncate_text(text)

        # Generate embedding (normalized to unit length -> better cosine)
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,   # <<<<<<<<<< مهم
            show_progress_bar=False
        )

        embedding_list = embedding.tolist()
        # Cache
        if len(self._embedding_cache) < self._cache_max_size:
            self._embedding_cache[key] = embedding_list

        return embedding_list  


    async def generate_chunk_embedding(
        self,
        chunk: KnowledgeChunk,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        يولد embedding لـ chunk فردي.
        
        Args:
            chunk: KnowledgeChunk instance
            save_to_db: Whether to save embedding to database
            
        Returns:
            Dict with success status and embedding info
        """
        try:
            logger.info(f"🔄 Generating embedding for chunk {chunk.id}")
            
            # Generate embedding
            start_time = datetime.utcnow()
            embedding = self._encode_text(chunk.content)
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Save to database if requested
            if save_to_db:
                chunk.embedding_vector = json.dumps(embedding)
                await self.db.commit()
                await self.db.refresh(chunk)
                logger.info(f"✅ Saved embedding for chunk {chunk.id}")
            
            return {
                "success": True,
                "chunk_id": chunk.id,
                "embedding_dimension": len(embedding),
                "processing_time": processing_time,
                "embedding": embedding
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding for chunk {chunk.id}: {str(e)}")
            return {
                "success": False,
                "chunk_id": chunk.id,
                "error": str(e)
            }
    
    async def generate_document_embeddings(
        self,
        document_id: int,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        يولد embeddings لكل الـ chunks في document معين.
        
        Args:
            document_id: ID of the document
            overwrite: Whether to overwrite existing embeddings
            
        Returns:
            Dict with processing statistics
        """
        try:
            logger.info(f"📄 Processing document {document_id}")
            
            # Get all chunks for this document
            query = select(KnowledgeChunk).where(
                KnowledgeChunk.document_id == document_id
            )
            
            # Filter out chunks that already have embeddings (unless overwrite)
            if not overwrite:
                query = query.where(
                    or_(
                        KnowledgeChunk.embedding_vector.is_(None),
                        KnowledgeChunk.embedding_vector == ''
                    )
                )
            
            result = await self.db.execute(query)
            chunks = result.scalars().all()
            
            if not chunks:
                logger.warning(f"⚠️ No chunks to process for document {document_id}")
                return {
                    "success": True,
                    "document_id": document_id,
                    "total_chunks": 0,
                    "processed_chunks": 0,
                    "failed_chunks": 0,
                    "processing_time": "0s"
                }
            
            logger.info(f"📦 Found {len(chunks)} chunks to process")
            
            # Process in batches
            start_time = datetime.utcnow()
            processed = 0
            failed = 0
            
            for i in range(0, len(chunks), self.batch_size):
                batch = chunks[i:i + self.batch_size]
                logger.info(f"⚙️ Processing batch {i // self.batch_size + 1}/{(len(chunks) + self.batch_size - 1) // self.batch_size}")
                
                # Extract texts
                texts = [chunk.content for chunk in batch]
                
                # Generate embeddings for batch
                self._ensure_model_loaded()
                embeddings = self.model.encode(
                    texts,
                    batch_size=len(batch),
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                
                # Save to database
                for chunk, embedding in zip(batch, embeddings):
                    try:
                        chunk.embedding_vector = json.dumps(embedding.tolist())
                        processed += 1
                    except Exception as e:
                        logger.error(f"❌ Failed to save embedding for chunk {chunk.id}: {str(e)}")
                        failed += 1
                
                # Commit batch
                await self.db.commit()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Document {document_id} processed: {processed} successful, {failed} failed")
            
            return {
                "success": True,
                "document_id": document_id,
                "total_chunks": len(chunks),
                "processed_chunks": processed,
                "failed_chunks": failed,
                "processing_time": f"{processing_time:.2f}s"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process document {document_id}: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e)
            }
    
    async def generate_batch_embeddings(
        self,
        chunk_ids: List[int],
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        يولد embeddings لمجموعة من الـ chunks.
        
        Args:
            chunk_ids: List of chunk IDs to process
            overwrite: Whether to overwrite existing embeddings
            
        Returns:
            Dict with processing statistics
        """
        try:
            logger.info(f"📦 Processing {len(chunk_ids)} chunks")
            
            # Get chunks
            query = select(KnowledgeChunk).where(
                KnowledgeChunk.id.in_(chunk_ids)
            )
            
            if not overwrite:
                query = query.where(
                    or_(
                        KnowledgeChunk.embedding_vector.is_(None),
                        KnowledgeChunk.embedding_vector == ''
                    )
                )
            
            result = await self.db.execute(query)
            chunks = result.scalars().all()
            
            if not chunks:
                return {
                    "success": True,
                    "total_chunks": 0,
                    "processed_chunks": 0,
                    "failed_chunks": 0,
                    "processing_time": "0s"
                }
            
            # Process in batches
            start_time = datetime.utcnow()
            processed = 0
            failed = 0
            
            for i in range(0, len(chunks), self.batch_size):
                batch = chunks[i:i + self.batch_size]
                
                texts = [chunk.content for chunk in batch]
                
                self._ensure_model_loaded()
                embeddings = self.model.encode(
                    texts,
                    batch_size=len(batch),
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                
                for chunk, embedding in zip(batch, embeddings):
                    try:
                        chunk.embedding_vector = json.dumps(embedding.tolist())
                        processed += 1
                    except Exception as e:
                        logger.error(f"❌ Failed to save embedding for chunk {chunk.id}: {str(e)}")
                        failed += 1
                
                await self.db.commit()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "success": True,
                "total_chunks": len(chunks),
                "processed_chunks": processed,
                "failed_chunks": failed,
                "processing_time": f"{processing_time:.2f}s"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to process batch: {str(e)}")
            await self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        يحسب التشابه بين embeddingين باستخدام cosine similarity.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate similarity: {str(e)}")
            return 0.0
    
    async def find_similar_chunks(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        يبحث عن الـ chunks الأكثر تشابهاً مع query.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            threshold: Minimum similarity threshold (0.0 to 1.0)
            filters: Optional filters (e.g., {"case_id": 123})
            
        Returns:
            List of similar chunks with similarity scores
        """
        try:
            logger.info(f"🔍 Searching for: '{query[:50]}...'")
            
            # Generate query embedding
            query_embedding = self._encode_text(query)
            
            # Get all chunks with embeddings
            query_builder = select(KnowledgeChunk).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != ''
                )
            )
            
            # Apply filters if provided
            if filters:
                if 'document_id' in filters:
                    query_builder = query_builder.where(
                        KnowledgeChunk.document_id == filters['document_id']
                    )
                if 'case_id' in filters:
                    query_builder = query_builder.where(
                        KnowledgeChunk.case_id == filters['case_id']
                    )
                if 'law_source_id' in filters:
                    query_builder = query_builder.where(
                        KnowledgeChunk.law_source_id == filters['law_source_id']
                    )
            
            result = await self.db.execute(query_builder)
            chunks = result.scalars().all()
            
            logger.info(f"📊 Found {len(chunks)} chunks with embeddings")
            
            if not chunks:
                return []
            
            # Calculate similarities
            similarities = []
            for chunk in chunks:
                try:
                    chunk_embedding = json.loads(chunk.embedding_vector)
                    similarity = self.calculate_similarity(query_embedding, chunk_embedding)
                    
                    if similarity >= threshold:
                        similarities.append({
                            "chunk_id": chunk.id,
                            "content": chunk.content,
                            "similarity": round(similarity, 4),
                            "document_id": chunk.document_id,
                            "chunk_index": chunk.chunk_index,
                            "law_source_id": chunk.law_source_id,
                            "case_id": chunk.case_id,
                            "article_id": chunk.article_id,
                            "tokens_count": chunk.tokens_count
                        })
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process chunk {chunk.id}: {str(e)}")
                    continue
            
            # Sort by similarity (descending) and take top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            results = similarities[:top_k]
            
            logger.info(f"✅ Found {len(results)} similar chunks above threshold {threshold}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to search for similar chunks: {str(e)}")
            return []
    
    async def get_embedding_status(self, document_id: int) -> Dict[str, Any]:
        """
        يعرض حالة الـ embeddings لـ document محدد.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dict with embedding statistics
        """
        try:
            # Get total chunks
            total_result = await self.db.execute(
                select(func.count(KnowledgeChunk.id)).where(
                    KnowledgeChunk.document_id == document_id
                )
            )
            total_chunks = total_result.scalar() or 0
            
            # Get chunks with embeddings
            with_embeddings_result = await self.db.execute(
                select(func.count(KnowledgeChunk.id)).where(
                    and_(
                        KnowledgeChunk.document_id == document_id,
                        KnowledgeChunk.embedding_vector.isnot(None),
                        KnowledgeChunk.embedding_vector != ''
                    )
                )
            )
            with_embeddings = with_embeddings_result.scalar() or 0
            
            # Calculate completion percentage
            completion = (with_embeddings / total_chunks * 100) if total_chunks > 0 else 0
            
            return {
                "success": True,
                "document_id": document_id,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": with_embeddings,
                "chunks_without_embeddings": total_chunks - with_embeddings,
                "completion_percentage": round(completion, 2),
                "status": "complete" if completion == 100 else "partial" if completion > 0 else "not_started"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get embedding status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_global_embedding_status(self) -> Dict[str, Any]:
        """
        يعرض حالة الـ embeddings لكل النظام.
        
        Returns:
            Dict with global embedding statistics
        """
        try:
            # Get total chunks
            total_result = await self.db.execute(
                select(func.count(KnowledgeChunk.id))
            )
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
            with_embeddings = with_embeddings_result.scalar() or 0
            
            # Calculate completion percentage
            completion = (with_embeddings / total_chunks * 100) if total_chunks > 0 else 0
            
            return {
                "success": True,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": with_embeddings,
                "chunks_without_embeddings": total_chunks - with_embeddings,
                "completion_percentage": round(completion, 2),
                "model_name": self.model_name,
                "device": self.device
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get global embedding status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }