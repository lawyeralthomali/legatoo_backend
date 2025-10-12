import logging
import json
import re
import numpy as np
import asyncio
import gc
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sentence_transformers import SentenceTransformer
import torch
from concurrent.futures import ThreadPoolExecutor

# Import global configuration
from ...config.embedding_config import EmbeddingConfig

# Memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("⚠️ psutil not available. Memory monitoring disabled.")

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Advanced Embedding Service for Arabic Legal Texts
    
    Features:
    - Optimized for Arabic legal text processing
    - Smart caching and batch processing
    - Enhanced text normalization for Arabic
    - Production-ready error handling
    - Memory-efficient operations
    """
    
    # Memory-optimized model configurations for Arabic legal texts
    MODELS = {
        'default': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        'large': 'intfloat/multilingual-e5-large',
        'small': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        'arabic': 'Ezzaldin-97/STS-Arabert',
        'legal_optimized': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',  # ⚡ MEMORY OPTIMIZED
        'ultra_small': 'sentence-transformers/all-MiniLM-L6-v2',  # 🚀 LOWEST MEMORY
        'arabic_small': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',  # 🎯 ARABIC + SMALL
        'no_ml': 'NO_ML_MODE'  # 🚫 NO ML - Hash-based fallback
    }
    
    def __init__(self, db: AsyncSession, model_name: Optional[str] = None):
        """
        Initialize the embedding service with memory optimization.
        
        Args:
            db: Async database session
            model_name: Name of the model to use (None = use global config)
        """
        self.db = db
        
        # 🔧 Use global configuration if model_name not specified
        if model_name is None:
            model_name = EmbeddingConfig.get_default_model()
        
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.device = 'cpu'  # 🔧 FORCE CPU to prevent CUDA memory issues
        
        # 🚫 NO-ML MODE: Check global configuration
        self.no_ml_mode = (model_name == 'no_ml' or EmbeddingConfig.is_ml_disabled())
        
        # Thread pool for blocking operations - reduced workers for memory
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        # 🚀 MEMORY-OPTIMIZED settings from global config
        self.batch_size = EmbeddingConfig.get_batch_size()
        self.max_seq_length = EmbeddingConfig.get_max_seq_length()
        self.normalize_embeddings = True
        
        # 🧹 REDUCED caching for memory from global config
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_max_size = EmbeddingConfig.get_cache_size()
        self._cache_hits = 0
        self._cache_misses = 0
        
        # 📝 Text processing settings
        self.max_text_length = 500  # Reduced from 2000
        self.min_text_length = 10
        
        # 🧠 Memory monitoring
        self._memory_usage_mb = 0
        
        if self.no_ml_mode:
            logger.info(f"🚫 EmbeddingService initialized in NO-ML MODE (no models will be loaded)")
            logger.info(f"💡 Using hash-based embeddings for memory safety")
        else:
            logger.info(f"🚀 EmbeddingService initialized with model: {model_name}")
            logger.info(f"📱 Device: {self.device} (forced CPU for memory safety)")
            logger.info(f"💾 Memory-optimized settings: batch_size={self.batch_size}, max_seq={self.max_seq_length}")

    def initialize_model(self) -> None:
        """
        Initialize the embedding model with memory-optimized settings.
        """
        if self.no_ml_mode:
            logger.info("🚫 NO-ML MODE: Skipping model initialization")
            self.model = None
            return
        
        try:
            # Check available memory if psutil is available
            if PSUTIL_AVAILABLE:
                memory = psutil.virtual_memory()
                available_gb = memory.available / (1024**3)
            else:
                available_gb = 4.0  # Assume 4GB if psutil unavailable
            
            logger.info(f"🧠 Available memory: {available_gb:.2f} GB")
            
            # If memory is very low, force NO-ML mode
            if available_gb < 1.5:
                logger.warning(f"⚠️ Very low memory ({available_gb:.2f} GB). Switching to NO-ML mode.")
                self.no_ml_mode = True
                self.model = None
                return
            
            if available_gb < 2.0:
                logger.warning(f"⚠️ Low memory ({available_gb:.2f} GB). Using ultra-small model.")
                model_name = 'ultra_small'
            else:
                model_name = self.model_name
            
            model_path = self.MODELS.get(model_name, self.MODELS['ultra_small'])
            
            logger.info(f"🔧 Loading memory-optimized model: {model_path}")
            
            # Force garbage collection before loading
            gc.collect()
            
            # Load model with memory-optimized settings
            self.model = SentenceTransformer(
                model_path,
                device=self.device,
                cache_folder=None  # Don't cache on disk to save space
            )
            
            # Configure model for memory efficiency
            self.model.max_seq_length = self.max_seq_length
            
            # Minimal warm-up (single word to save memory)
            try:
                test_embedding = self.model.encode(["test"], convert_to_numpy=True, show_progress_bar=False)
                logger.info(f"✅ Model initialized successfully")
                logger.info(f"   Dimension: {len(test_embedding[0])}")
                logger.info(f"   Max sequence length: {self.model.max_seq_length}")
                if PSUTIL_AVAILABLE:
                    memory_used = psutil.Process().memory_info().rss / (1024**2)
                    logger.info(f"   Memory used: ~{memory_used:.1f} MB")
                
                # Clear test embedding
                del test_embedding
                gc.collect()
                
            except Exception as warmup_error:
                logger.warning(f"⚠️ Model warm-up failed: {warmup_error}")
                logger.info("✅ Model loaded but warm-up skipped for memory")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding model: {str(e)}")
            logger.warning("🚫 Switching to NO-ML mode due to model loading failure")
            self.no_ml_mode = True
            self.model = None

    async def initialize(self) -> None:
        """
        Async wrapper for model initialization to prevent blocking.
        This is the method that should be called from async contexts.
        """
        if self.model is None:
            logger.info("🔄 Loading embedding model asynchronously...")
            # Run blocking model initialization in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, self.initialize_model)
            logger.info("✅ Model loaded successfully in async context")
    
    def _ensure_model_loaded(self) -> None:
        """Ensure model is loaded with thread safety."""
        if self.model is None:
            self.initialize_model()

    def _normalize_arabic_text(self, text: str) -> str:
        """
        Enhanced Arabic text normalization for legal documents.
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Remove Arabic diacritics (tashkeel)
        arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
        text = arabic_diacritics.sub('', text)
        
        # Normalize Arabic character variants
        text = re.sub(r'[إأآا]', 'ا', text)  # Alif variants
        text = re.sub(r'ى', 'ي', text)       # Ya variants
        text = re.sub(r'ة', 'ه', text)       # Ta marbuta
        text = re.sub(r'ؤ', 'ء', text)       # Hamza variants
        text = re.sub(r'ئ', 'ء', text)       # Hamza variants
        
        # Remove special characters but preserve Arabic and basic punctuation
        text = re.sub(r'[^\w\u0600-\u06FF\s.,!?؛،]', ' ', text)
        
        return text.strip()

    def _truncate_text_smart(self, text: str, max_tokens: int = 500) -> str:
        """
        Smart text truncation that preserves meaning for Arabic legal texts.
        """
        if not text:
            return ""
            
        # First normalize the text
        normalized = self._normalize_arabic_text(text)
        
        # Simple word-based truncation (more reliable for Arabic)
        words = normalized.split()
        
        if len(words) <= max_tokens:
            return normalized
        
        # Smart truncation: take beginning, middle, and end for context preservation
        start_words = words[:max_tokens // 3]
        middle_start = len(words) // 2 - max_tokens // 6
        middle_end = len(words) // 2 + max_tokens // 6
        middle_words = words[max(middle_start, 0):min(middle_end, len(words))]
        end_words = words[-max_tokens // 3:]
        
        # Combine and ensure we don't exceed max_tokens
        selected_words = start_words + middle_words + end_words
        if len(selected_words) > max_tokens:
            selected_words = selected_words[:max_tokens]
        
        truncated = " ".join(selected_words)
        
        logger.debug(f"📝 Smart truncation: {len(words)} → {len(selected_words)} words")
        
        return truncated

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key with enhanced normalization.
        """
        if not text:
            return ""
        
        # Enhanced normalization for cache key
        normalized = self._normalize_arabic_text(text)
        # Remove extra spaces and limit length for key
        key = re.sub(r'\s+', ' ', normalized).strip()[:500]
        return key

    def _generate_hash_embedding(self, text: str) -> List[float]:
        """
        Generate a deterministic hash-based embedding for NO-ML mode.
        This creates a fixed-size vector from text hash for similarity calculations.
        """
        import hashlib
        
        if not text:
            return [0.0] * 256  # Standard embedding dimension
        
        # Normalize text
        processed_text = self._normalize_arabic_text(text)
        processed_text = self._truncate_text_smart(processed_text, max_tokens=100)
        
        # Create hash-based embedding
        text_hash = hashlib.sha256(processed_text.encode('utf-8')).hexdigest()
        
        # Convert hash to vector (deterministic)
        embedding = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0  # Normalize to [0,1]
            embedding.append(value)
        
        # Pad to 256 dimensions
        while len(embedding) < 256:
            embedding.append(0.0)
        
        return embedding[:256]
    
    def _encode_text_sync(self, text: str) -> List[float]:
        """
        Synchronous encoding - should be called from thread pool.
        Encode text to embedding vector with enhanced Arabic support.
        """
        if self.no_ml_mode:
            return self._generate_hash_embedding(text)
        
        self._ensure_model_loaded()
        
        if not text or len(text.strip()) < self.min_text_length:
            logger.warning("⚠️ Text too short for embedding")
            return [0.0] * 256  # Standard dimension
        
        # Generate cache key
        cache_key = self._get_cache_key(text)
        
        # Check cache
        if cache_key and cache_key in self._embedding_cache:
            self._cache_hits += 1
            logger.debug("📦 Using cached embedding")
            return self._embedding_cache[cache_key]
        
        self._cache_misses += 1
        
        try:
            # Preprocess text
            processed_text = self._normalize_arabic_text(text)
            processed_text = self._truncate_text_smart(processed_text)
            
            if not processed_text or len(processed_text.strip()) < self.min_text_length:
                logger.warning("⚠️ Processed text too short")
                return [0.0] * 256
            
            # Generate embedding - THIS IS THE BLOCKING OPERATION
            embedding = self.model.encode(
                processed_text,
                convert_to_numpy=True,
                normalize_embeddings=self.normalize_embeddings,
                show_progress_bar=False,
                batch_size=1
            )
            
            embedding_list = embedding.tolist()
            
            # Cache the result
            if cache_key and len(self._embedding_cache) < self._cache_max_size:
                self._embedding_cache[cache_key] = embedding_list
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {str(e)}")
            logger.warning("🚫 Falling back to hash-based embedding")
            return self._generate_hash_embedding(text)

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text (async wrapper).
        Runs encoding in thread pool to prevent blocking.
        """
        if self.model is None:
            await self.initialize()
        
        # Run blocking encoding in thread pool
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(self._executor, self._encode_text_sync, text)
        return embedding

    def _encode_batch_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Memory-optimized synchronous batch encoding.
        """
        if not texts:
            return []
        
        if self.no_ml_mode:
            # Generate hash-based embeddings for all texts
            embeddings = []
            for text in texts:
                embeddings.append(self._generate_hash_embedding(text))
            logger.info(f"✅ Generated {len(embeddings)} hash-based embeddings (NO-ML mode)")
            return embeddings
        
        self._ensure_model_loaded()
        
        try:
            
            # Preprocess all texts with memory optimization
            processed_texts = []
            valid_indices = []
            
            for i, text in enumerate(texts):
                processed = self._normalize_arabic_text(text)
                processed = self._truncate_text_smart(processed, max_tokens=100)  # Reduced token limit
                
                if processed and len(processed.strip()) >= self.min_text_length:
                    processed_texts.append(processed)
                    valid_indices.append(i)
            
            if not processed_texts:
                logger.warning("⚠️ No valid texts for batch embedding")
                return []
            
            # 🚀 MEMORY-OPTIMIZED batch processing
            all_embeddings = []
            
            # Process in very small batches to prevent OOM
            mini_batch_size = min(2, self.batch_size)  # Maximum 2 texts at once
            
            for i in range(0, len(processed_texts), mini_batch_size):
                batch_texts = processed_texts[i:i + mini_batch_size]
                
                try:
                    # Generate embeddings with memory optimization
                    batch_embeddings = self.model.encode(
                        batch_texts,
                        convert_to_numpy=True,
                        normalize_embeddings=self.normalize_embeddings,
                        show_progress_bar=False,
                        batch_size=1  # Force batch size 1 for memory safety
                    )
                    
                    # Convert to list and free numpy array immediately
                    embeddings_list = batch_embeddings.tolist()
                    del batch_embeddings
                    
                    all_embeddings.extend(embeddings_list)
                    
                    # Force garbage collection after each mini-batch
                    gc.collect()
                    
                    logger.debug(f"📦 Processed mini-batch {i//mini_batch_size + 1}")
                    
                except Exception as batch_error:
                    logger.error(f"❌ Mini-batch {i//mini_batch_size + 1} failed: {batch_error}")
                    # Add hash-based embeddings for failed batch
                    for text in batch_texts:
                        all_embeddings.append(self._generate_hash_embedding(text))
            
            # Map back to original indices
            result = [[]] * len(texts)
            for idx, embedding in zip(valid_indices, all_embeddings):
                result[idx] = embedding
            
            # Fill missing indices with hash-based embeddings
            for i in range(len(result)):
                if not result[i]:
                    result[i] = self._generate_hash_embedding(texts[i])
            
            # Final cleanup
            del all_embeddings, processed_texts
            gc.collect()
            
            logger.info(f"✅ Generated {len(valid_indices)} embeddings from {len(texts)} texts (memory-optimized)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Batch embedding generation failed: {str(e)}")
            logger.warning("🚫 Falling back to hash-based embeddings for all texts")
            # Return hash-based embeddings for all texts
            return [self._generate_hash_embedding(text) for text in texts]
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts with optimized processing.
        Runs encoding in thread pool to prevent blocking.
        """
        if not texts:
            return []
        
        if self.model is None:
            await self.initialize()
        
        # Run blocking batch encoding in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(self._executor, self._encode_batch_sync, texts)
        return embeddings
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Alias for generate_batch_embeddings for backward compatibility.
        """
        return await self.generate_batch_embeddings(texts)

    async def generate_chunk_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for multiple chunks with metadata.
        """
        if not chunks:
            return []
        
        try:
            # Extract texts for batch processing
            texts = [chunk.get('content', '') for chunk in chunks]
            embeddings = await self.generate_batch_embeddings(texts)
            
            # Combine results with original chunk data
            results = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if embedding:  # Only include successful embeddings
                    results.append({
                        **chunk,
                        'embedding': embedding,
                        'embedding_dimension': len(embedding),
                        'processed_at': datetime.utcnow().isoformat()
                    })
                else:
                    logger.warning(f"⚠️ Failed to generate embedding for chunk {i}")
            
            logger.info(f"✅ Processed {len(results)}/{len(chunks)} chunks successfully")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Chunk embedding generation failed: {str(e)}")
            return []

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        """
        try:
            if not embedding1 or not embedding2:
                return 0.0
            
            vec1 = np.array(embedding1, dtype=np.float32)
            vec2 = np.array(embedding2, dtype=np.float32)
            
            # Handle zero vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Cosine similarity
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            
            # Clamp to [0, 1] range
            return float(max(0.0, min(1.0, similarity)))
            
        except Exception as e:
            logger.error(f"❌ Similarity calculation failed: {str(e)}")
            return 0.0
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Alias for calculate_similarity for backward compatibility.
        """
        return self.calculate_similarity(embedding1, embedding2)

    def calculate_batch_similarities(self, query_embedding: List[float], 
                                   chunk_embeddings: List[List[float]]) -> np.ndarray:
        """
        Calculate similarities between query and multiple chunks efficiently.
        """
        if not query_embedding or not chunk_embeddings:
            return np.array([])
        
        try:
            query_vec = np.array(query_embedding, dtype=np.float32)
            query_norm = np.linalg.norm(query_vec)
            
            if query_norm == 0:
                return np.zeros(len(chunk_embeddings))
            
            # Convert to numpy array
            chunk_array = np.array(chunk_embeddings, dtype=np.float32)
            
            # Calculate norms
            chunk_norms = np.linalg.norm(chunk_array, axis=1)
            valid_mask = chunk_norms > 0
            
            # Initialize result array
            similarities = np.zeros(len(chunk_embeddings))
            
            if np.any(valid_mask):
                # Calculate cosine similarities for valid embeddings
                valid_chunks = chunk_array[valid_mask]
                valid_norms = chunk_norms[valid_mask]
                
                dot_products = np.dot(valid_chunks, query_vec)
                valid_similarities = dot_products / (valid_norms * query_norm)
                
                # Clamp to [0, 1] and assign to result
                similarities[valid_mask] = np.clip(valid_similarities, 0.0, 1.0)
            
            return similarities
            
        except Exception as e:
            logger.error(f"❌ Batch similarity calculation failed: {str(e)}")
            return np.zeros(len(chunk_embeddings))

    async def find_similar_chunks(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 10,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Find chunks similar to query with enhanced filtering.
        """
        if not query or not chunks:
            return []
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            if not query_embedding or np.linalg.norm(query_embedding) == 0:
                logger.warning("⚠️ Query embedding is zero vector")
                return []
            
            # Extract chunk embeddings
            chunk_embeddings = []
            valid_chunks = []
            
            for chunk in chunks:
                embedding_str = chunk.get('embedding_vector')
                if embedding_str:
                    try:
                        embedding = json.loads(embedding_str)
                        if embedding and len(embedding) > 0:
                            chunk_embeddings.append(embedding)
                            valid_chunks.append(chunk)
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            if not chunk_embeddings:
                return []
            
            # Calculate similarities
            similarities = self.calculate_batch_similarities(query_embedding, chunk_embeddings)
            
            # Filter and sort results
            results = []
            for i, similarity in enumerate(similarities):
                if similarity >= threshold:
                    chunk = valid_chunks[i]
                    results.append({
                        'chunk_id': chunk.get('id'),
                        'content': chunk.get('content', ''),
                        'similarity_score': round(float(similarity), 4),
                        'law_source_id': chunk.get('law_source_id'),
                        'word_count': chunk.get('tokens_count', 0),
                        'metadata': chunk.get('metadata', {})
                    })
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Take top_k
            final_results = results[:top_k]
            
            logger.info(f"✅ Found {len(final_results)} similar chunks (threshold: {threshold})")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Similar chunk search failed: {str(e)}")
            return []

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get embedding service statistics and health status.
        """
        if self.model is None:
            await self.initialize()
        
        cache_info = {
            'cache_size': len(self._embedding_cache),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / (self._cache_hits + self._cache_misses) 
                if (self._cache_hits + self._cache_misses) > 0 else 0
        }
        
        model_info = {
            'model_name': self.model_name,
            'model_dimension': self.model.get_sentence_embedding_dimension(),
            'max_sequence_length': self.model.max_seq_length,
            'device': self.device,
            'normalize_embeddings': self.normalize_embeddings
        }
        
        performance_info = {
            'batch_size': self.batch_size,
            'max_text_length': self.max_text_length,
            'min_text_length': self.min_text_length
        }
        
        return {
            'status': 'healthy',
            'cache': cache_info,
            'model': model_info,
            'performance': performance_info,
            'timestamp': datetime.utcnow().isoformat()
        }

    def clear_cache(self) -> Dict[str, Any]:
        """
        Clear the embedding cache and return statistics.
        """
        cache_stats = {
            'cleared_entries': len(self._embedding_cache),
            'previous_hits': self._cache_hits,
            'previous_misses': self._cache_misses
        }
        
        self._embedding_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.info("🧹 Embedding cache cleared")
        
        return cache_stats

    async def validate_embedding_quality(self, sample_texts: List[str] = None) -> Dict[str, Any]:
        """
        Validate embedding quality with sample texts.
        """
        if sample_texts is None:
            sample_texts = [
                "نص قانوني تجريبي للتحقق من جودة التضمين",
                "تحليل النصوص القانونية العربية",
                "بحث في التشريعات واللوائح"
            ]
        
        try:
            # Ensure model is loaded asynchronously
            if self.model is None:
                await self.initialize()
            
            # Generate embeddings for sample texts
            embeddings = await self.generate_batch_embeddings(sample_texts)
            
            # Calculate self-similarities
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    if embeddings[i] and embeddings[j]:
                        sim = self.calculate_similarity(embeddings[i], embeddings[j])
                        similarities.append(sim)
            
            # Calculate statistics
            if similarities:
                avg_similarity = np.mean(similarities)
                std_similarity = np.std(similarities)
            else:
                avg_similarity = 0.0
                std_similarity = 0.0
            
            quality_metrics = {
                'sample_texts_processed': len([e for e in embeddings if e]),
                'average_similarity': round(float(avg_similarity), 4),
                'similarity_std': round(float(std_similarity), 4),
                'embedding_dimension': self.model.get_sentence_embedding_dimension(),
                'all_embeddings_valid': all(embeddings)
            }
            
            logger.info(f"✅ Embedding quality validation completed")
            
            return {
                'success': True,
                'quality_metrics': quality_metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Embedding quality validation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }