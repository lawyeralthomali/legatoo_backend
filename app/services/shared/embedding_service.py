"""
Embedding service for Arabic legal texts with memory optimization and NO-ML fallback.
Production-ready with caching, batch processing, and async support.
"""

import logging
import json
import re
import hashlib
import numpy as np
import asyncio
import gc
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer

from ...config.embedding_config import EmbeddingConfig

# Memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Constants
MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 500
HASH_EMBEDDING_DIM = 256
MIN_MEMORY_GB = 1.5
LOW_MEMORY_GB = 2.0


class EmbeddingService:
    """Embedding service with memory optimization, caching, and Arabic support."""
    
    MODELS = {
        'default': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        'large': 'intfloat/multilingual-e5-large',
        'small': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        'arabic': 'Ezzaldin-97/STS-Arabert',
        'legal_optimized': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        'ultra_small': 'sentence-transformers/all-MiniLM-L6-v2',
        'no_ml': 'NO_ML_MODE'
    }
    
    def __init__(self, db: AsyncSession, model_name: Optional[str] = None):
        """Initialize embedding service with configuration."""
        self.db = db
        self.model_name = model_name or EmbeddingConfig.get_default_model()
        self.model: Optional[SentenceTransformer] = None
        self.device = 'cpu'
        
        # NO-ML mode check
        self.no_ml_mode = (
            self.model_name == 'no_ml' or 
            EmbeddingConfig.is_ml_disabled()
        )
        
        # Thread pool for blocking operations
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        # Settings
        self.batch_size = EmbeddingConfig.get_batch_size()
        self.max_seq_length = EmbeddingConfig.get_max_seq_length()
        self.normalize_embeddings = True
        
        # Caching
        self._cache: Dict[str, List[float]] = {}
        self._cache_max = EmbeddingConfig.get_cache_size()
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info(f"EmbeddingService initialized: model={self.model_name}, no_ml={self.no_ml_mode}")
    
    # === Internal Helpers ===
    
    def _get_available_memory(self) -> float:
        """Get available memory in GB."""
        if PSUTIL_AVAILABLE:
            return psutil.virtual_memory().available / (1024**3)
        return 4.0
    
    def _normalize_arabic_text(self, text: str) -> str:
        """Normalize Arabic text: remove diacritics and normalize character variants."""
        if not text or not isinstance(text, str):
            return ""
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove diacritics
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        
        # Normalize variants
        text = re.sub(r'[إأآا]', 'ا', text)
        text = re.sub(r'ى', 'ي', text)
        text = re.sub(r'ة', 'ه', text)
        text = re.sub(r'[ؤئ]', 'ء', text)
        
        # Keep only Arabic, alphanumeric, and basic punctuation
        text = re.sub(r'[^\w\u0600-\u06FF\s.,!?؛،]', ' ', text)
        
        return text.strip()
    
    def _preprocess_text(self, text: str, max_tokens: int = MAX_TEXT_LENGTH) -> str:
        """Normalize and truncate text in single pass."""
        if not text:
            return ""
        
        # Normalize
        normalized = self._normalize_arabic_text(text)
        words = normalized.split()
        
        # Truncate if needed
        if len(words) <= max_tokens:
            return normalized
        
        # Smart truncation: beginning + middle + end
        third = max_tokens // 3
        start = words[:third]
        mid_idx = len(words) // 2
        middle = words[mid_idx - third//2:mid_idx + third//2]
        end = words[-third:]
        
        return " ".join((start + middle + end)[:max_tokens])
    
    def _generate_hash_embedding(self, text: str) -> List[float]:
        """Generate deterministic hash-based embedding for NO-ML mode."""
        if not text:
            return [0.0] * HASH_EMBEDDING_DIM
        
        # Process and hash
        processed = self._preprocess_text(text, max_tokens=100)
        text_hash = hashlib.sha256(processed.encode('utf-8')).hexdigest()
        
        # Convert to vector
        embedding = [int(text_hash[i:i+2], 16) / 255.0 for i in range(0, len(text_hash), 2)]
        
        # Pad to dimension
        while len(embedding) < HASH_EMBEDDING_DIM:
            embedding.append(0.0)
        
        return embedding[:HASH_EMBEDDING_DIM]
    
    def _encode_text_sync(self, text: str) -> List[float]:
        """Synchronous single text encoding with caching."""
        # NO-ML mode
        if self.no_ml_mode:
            return self._generate_hash_embedding(text)
        
        # Initialize if needed
        if self.model is None:
            self.initialize_model()
        
        # Check length
        if not text or len(text.strip()) < MIN_TEXT_LENGTH:
            return [0.0] * HASH_EMBEDDING_DIM
        
        # Check cache
        cache_key = self._preprocess_text(text)
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
        
        self._cache_misses += 1
        
        try:
            # Preprocess
            processed = self._preprocess_text(text)
            
            if not processed or len(processed.strip()) < MIN_TEXT_LENGTH:
                return [0.0] * HASH_EMBEDDING_DIM
            
            # Encode
            embedding = self.model.encode(
                processed,
                convert_to_numpy=True,
                normalize_embeddings=self.normalize_embeddings,
                show_progress_bar=False,
                batch_size=1
            )
            
            embedding_list = embedding.tolist()
            
            # Cache
            if len(self._cache) < self._cache_max:
                self._cache[cache_key] = embedding_list
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return self._generate_hash_embedding(text)
    
    def _encode_batch_sync(self, texts: List[str]) -> List[List[float]]:
        """Memory-optimized batch encoding."""
        if not texts:
            return []
        
        # NO-ML mode
        if self.no_ml_mode:
            return [self._generate_hash_embedding(t) for t in texts]
        
        # Initialize if needed
        if self.model is None:
            self.initialize_model()
        
        try:
            # Preprocess
            processed = []
            valid_idx = []
            
            for i, text in enumerate(texts):
                proc = self._preprocess_text(text, max_tokens=100)
                if proc and len(proc.strip()) >= MIN_TEXT_LENGTH:
                    processed.append(proc)
                    valid_idx.append(i)
            
            if not processed:
                return [[0.0] * HASH_EMBEDDING_DIM] * len(texts)
            
            # Process in mini-batches
            all_emb = []
            mini_batch = min(2, self.batch_size)
            
            for i in range(0, len(processed), mini_batch):
                batch = processed[i:i + mini_batch]
                
                try:
                    # Encode mini-batch
                    batch_emb = self.model.encode(
                        batch,
                        convert_to_numpy=True,
                        normalize_embeddings=self.normalize_embeddings,
                        show_progress_bar=False,
                        batch_size=1
                    )
                    all_emb.extend(batch_emb.tolist())
                    del batch_emb
                except Exception as e:
                    logger.error(f"Mini-batch failed: {e}")
                    all_emb.extend([self._generate_hash_embedding(t) for t in batch])
                
                gc.collect()
            
            # Map back to original indices
            result = [[0.0] * HASH_EMBEDDING_DIM] * len(texts)
            for idx, emb in zip(valid_idx, all_emb):
                result[idx] = emb
            
            # Fill missing
            for i in range(len(result)):
                if all(v == 0.0 for v in result[i]):
                    result[i] = self._generate_hash_embedding(texts[i])
            
            return result
            
        except Exception as e:
            logger.error(f"Batch encoding failed: {e}")
            return [self._generate_hash_embedding(t) for t in texts]
    
    # === Public API ===
    
    def initialize_model(self) -> None:
        """Initialize embedding model with memory checks."""
        if self.no_ml_mode:
            return
        
        try:
            available_gb = self._get_available_memory()
            
            # Check memory
            if available_gb < MIN_MEMORY_GB:
                logger.warning(f"Low memory ({available_gb:.2f} GB), switching to NO-ML")
                self.no_ml_mode = True
                self.model = None
                return
            
            # Select model
            if available_gb < LOW_MEMORY_GB:
                model_name = 'ultra_small'
            else:
                model_name = self.model_name
            
            model_path = self.MODELS.get(model_name, self.MODELS['ultra_small'])
            
            gc.collect()
            
            # Load model
            self.model = SentenceTransformer(model_path, device=self.device, cache_folder=None)
            self.model.max_seq_length = self.max_seq_length
            
            # Warm-up
            try:
                test = self.model.encode(["test"], convert_to_numpy=True, show_progress_bar=False)
                logger.info(f"Model ready: dim={len(test[0])}")
                del test
                gc.collect()
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"Model init failed: {e}")
            self.no_ml_mode = True
            self.model = None
    
    async def initialize(self) -> None:
        """Async model initialization."""
        if self.model is None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, self.initialize_model)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        if self.model is None:
            await self.initialize()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._encode_text_sync, text)
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts."""
        if not texts:
            return []
        
        if self.model is None:
            await self.initialize()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._encode_batch_sync, texts)
    
    async def generate_chunk_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for chunks with metadata."""
        if not chunks:
            return []
        
        texts = [c.get('content', '') for c in chunks]
        embeddings = await self.generate_batch_embeddings(texts)
        
        results = []
        for chunk, emb in zip(chunks, embeddings):
            if emb and any(v != 0.0 for v in emb):
                results.append({
                    **chunk,
                    'embedding': emb,
                    'embedding_dimension': len(emb),
                    'processed_at': datetime.utcnow().isoformat()
                })
        
        return results
    
    def calculate_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        if not emb1 or not emb2:
            return 0.0
        
        try:
            v1 = np.array(emb1, dtype=np.float32)
            v2 = np.array(emb2, dtype=np.float32)
            
            n1 = np.linalg.norm(v1)
            n2 = np.linalg.norm(v2)
            
            if n1 == 0 or n2 == 0:
                return 0.0
            
            sim = np.dot(v1, v2) / (n1 * n2)
            return float(max(0.0, min(1.0, sim)))
            
        except Exception as e:
            logger.error(f"Similarity calc failed: {e}")
            return 0.0
    
    def calculate_batch_similarities(
        self, 
        query_emb: List[float], 
        chunk_embs: List[List[float]]
    ) -> np.ndarray:
        """Calculate similarities between query and multiple chunks."""
        if not query_emb or not chunk_embs:
            return np.array([])
        
        try:
            q = np.array(query_emb, dtype=np.float32)
            q_norm = np.linalg.norm(q)
            
            if q_norm == 0:
                return np.zeros(len(chunk_embs))
            
            chunks = np.array(chunk_embs, dtype=np.float32)
            norms = np.linalg.norm(chunks, axis=1)
            valid = norms > 0
            
            sims = np.zeros(len(chunk_embs))
            
            if np.any(valid):
                dots = np.dot(chunks[valid], q)
                sims[valid] = np.clip(dots / (norms[valid] * q_norm), 0.0, 1.0)
            
            return sims
            
        except Exception as e:
            logger.error(f"Batch similarity failed: {e}")
            return np.zeros(len(chunk_embs))
    
    async def find_similar_chunks(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 10,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Find similar chunks to query."""
        if not query or not chunks:
            return []
        
        try:
            q_emb = await self.generate_embedding(query)
            
            if not q_emb or np.linalg.norm(q_emb) == 0:
                return []
            
            # Extract embeddings
            chunk_embs = []
            valid = []
            
            for chunk in chunks:
                emb_str = chunk.get('embedding_vector')
                if emb_str:
                    try:
                        emb = json.loads(emb_str)
                        if emb and len(emb) > 0:
                            chunk_embs.append(emb)
                            valid.append(chunk)
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            if not chunk_embs:
                return []
            
            # Calculate similarities
            sims = self.calculate_batch_similarities(q_emb, chunk_embs)
            
            # Filter and format
            results = []
            for i, sim in enumerate(sims):
                if sim >= threshold:
                    c = valid[i]
                    results.append({
                        'chunk_id': c.get('id'),
                        'content': c.get('content', ''),
                        'similarity_score': round(float(sim), 4),
                        'law_source_id': c.get('law_source_id'),
                        'word_count': c.get('tokens_count', 0),
                        'metadata': c.get('metadata', {})
                    })
            
            # Sort and limit
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Similar chunks failed: {e}")
            return []
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get service statistics and health status."""
        if self.model is None and not self.no_ml_mode:
            await self.initialize()
        
        total = self._cache_hits + self._cache_misses
        
        # Model info
        if self.no_ml_mode:
            model_info = {
                'model_name': 'NO_ML_MODE',
                'model_dimension': HASH_EMBEDDING_DIM,
                'max_sequence_length': 0,
                'device': 'none',
                'normalize_embeddings': False
            }
        else:
            model_info = {
                'model_name': self.model_name,
                'model_dimension': self.model.get_sentence_embedding_dimension(),
                'max_sequence_length': self.model.max_seq_length,
                'device': self.device,
                'normalize_embeddings': self.normalize_embeddings
            }
        
        return {
            'status': 'healthy',
            'cache': {
                'size': len(self._cache),
                'hits': self._cache_hits,
                'misses': self._cache_misses,
                'hit_rate': self._cache_hits / total if total > 0 else 0
            },
            'model': model_info,
            'performance': {
                'batch_size': self.batch_size,
                'max_text_length': MAX_TEXT_LENGTH,
                'min_text_length': MIN_TEXT_LENGTH
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear cache and return stats."""
        stats = {
            'cleared_entries': len(self._cache),
            'previous_hits': self._cache_hits,
            'previous_misses': self._cache_misses
        }
        
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info("Cache cleared")
        return stats
    
    async def validate_embedding_quality(
        self, 
        sample_texts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate embedding quality with sample texts."""
        if sample_texts is None:
            sample_texts = [
                "نص قانوني تجريبي للتحقق من جودة التضمين",
                "تحليل النصوص القانونية العربية",
                "بحث في التشريعات واللوائح"
            ]
        
        try:
            if self.model is None:
                await self.initialize()
            
            embeddings = await self.generate_batch_embeddings(sample_texts)
            
            # Calculate pairwise similarities
            sims = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    if embeddings[i] and embeddings[j]:
                        sims.append(self.calculate_similarity(embeddings[i], embeddings[j]))
            
            dim = HASH_EMBEDDING_DIM if self.no_ml_mode else self.model.get_sentence_embedding_dimension()
            
            return {
                'success': True,
                'quality_metrics': {
                    'sample_texts_processed': len([e for e in embeddings if e]),
                    'average_similarity': round(float(np.mean(sims)) if sims else 0.0, 4),
                    'similarity_std': round(float(np.std(sims)) if sims else 0.0, 4),
                    'embedding_dimension': dim,
                    'all_embeddings_valid': all(embeddings)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
