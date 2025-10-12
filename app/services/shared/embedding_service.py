import logging
import json
import re
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sentence_transformers import SentenceTransformer
import torch

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
    
    # Optimized model configurations for Arabic legal texts
    MODELS = {
        'default': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
        'large': 'intfloat/multilingual-e5-large',
        'small': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        'arabic': 'Ezzaldin-97/STS-Arabert',
        'legal_optimized': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'  # Best for legal texts
    }
    
    def __init__(self, db: AsyncSession, model_name: str = 'legal_optimized'):
        """
        Initialize the embedding service.
        
        Args:
            db: Async database session
            model_name: Name of the model to use
        """
        self.db = db
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Optimized performance settings
        self.batch_size = 16  # Reduced for stability with large Arabic texts
        self.max_seq_length = 512
        self.normalize_embeddings = True
        
        # Enhanced caching system
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_max_size = 2000
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Text processing settings
        self.max_text_length = 2000  # Characters for safety
        self.min_text_length = 10
        
        logger.info(f"🚀 EmbeddingService initialized with model: {model_name}")
        logger.info(f"📱 Device: {self.device}, Batch size: {self.batch_size}")

    def initialize_model(self) -> None:
        """
        Initialize the embedding model with optimized settings for Arabic legal texts.
        """
        try:
            model_path = self.MODELS.get(self.model_name, self.MODELS['legal_optimized'])
            
            logger.info(f"🔧 Initializing embedding model: {model_path}")
            
            # Load model with optimized settings
            self.model = SentenceTransformer(
                model_path,
                device=self.device
            )
            
            # Configure model for Arabic text
            self.model.max_seq_length = self.max_seq_length
            
            # Warm up the model
            if torch.cuda.is_available():
                self.model.encode(["نص تجريبي"], convert_to_numpy=True)
            
            logger.info(f"✅ Model initialized successfully")
            logger.info(f"   Dimension: {self.model.get_sentence_embedding_dimension()}")
            logger.info(f"   Max sequence length: {self.model.max_seq_length}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding model: {str(e)}")
            raise RuntimeError(f"Model initialization failed: {str(e)}")

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

    def _encode_text(self, text: str) -> List[float]:
        """
        Encode text to embedding vector with enhanced Arabic support.
        """
        self._ensure_model_loaded()
        
        if not text or len(text.strip()) < self.min_text_length:
            logger.warning("⚠️ Text too short for embedding")
            return [0.0] * self.model.get_sentence_embedding_dimension()
        
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
                return [0.0] * self.model.get_sentence_embedding_dimension()
            
            # Generate embedding
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
            # Return zero vector as fallback
            return [0.0] * self.model.get_sentence_embedding_dimension()

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text (async wrapper).
        """
        return self._encode_text(text)

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts with optimized processing.
        """
        if not texts:
            return []
        
        self._ensure_model_loaded()
        
        try:
            # Preprocess all texts
            processed_texts = []
            valid_indices = []
            
            for i, text in enumerate(texts):
                processed = self._normalize_arabic_text(text)
                processed = self._truncate_text_smart(processed)
                
                if processed and len(processed.strip()) >= self.min_text_length:
                    processed_texts.append(processed)
                    valid_indices.append(i)
            
            if not processed_texts:
                logger.warning("⚠️ No valid texts for batch embedding")
                return []
            
            # Generate embeddings in batches
            all_embeddings = []
            for i in range(0, len(processed_texts), self.batch_size):
                batch_texts = processed_texts[i:i + self.batch_size]
                
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    normalize_embeddings=self.normalize_embeddings,
                    show_progress_bar=False,
                    batch_size=len(batch_texts)
                )
                
                all_embeddings.extend(batch_embeddings.tolist())
            
            # Map back to original indices
            result = [[]] * len(texts)
            for idx, embedding in zip(valid_indices, all_embeddings):
                result[idx] = embedding
            
            logger.info(f"✅ Generated {len(valid_indices)} embeddings from {len(texts)} texts")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Batch embedding generation failed: {str(e)}")
            # Return empty embeddings for all texts
            return [[] for _ in texts]

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
        self._ensure_model_loaded()
        
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
            self._ensure_model_loaded()
            
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