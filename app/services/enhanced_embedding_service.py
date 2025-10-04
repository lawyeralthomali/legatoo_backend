"""
Enhanced Embedding Service - Phase 4 Implementation

This service handles:
- Multiple embedding providers (OpenAI, HuggingFace)
- Batch embedding generation
- Retry logic and fallback
- Embedding dimension detection
- SQLite-compatible JSON storage

Supports:
- OpenAI: text-embedding-3-large (3072-dim)
- HuggingFace: paraphrase-multilingual-mpnet-base-v2 (768-dim)
- Custom models via sentence-transformers
"""

import logging
import os
from typing import List, Optional
import asyncio
import httpx
import numpy as np
from sentence_transformers import SentenceTransformer

# Optional tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Enum for embedding providers."""
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


class EnhancedEmbeddingService:
    """
    Enhanced embedding service with multiple providers.
    
    Phase 4 Implementation:
    - Supports OpenAI and HuggingFace embeddings
    - Automatic provider fallback
    - Batch processing
    - Retry logic
    """

    def __init__(self, provider: str = None):
        """
        Initialize embedding service.
        
        Args:
            provider: Embedding provider ('openai', 'huggingface', 'local')
                     If None, auto-detects based on API keys
        """
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        self.openai_base_url = "https://api.openai.com/v1/embeddings"
        
        # HuggingFace model (multilingual support for Arabic + English)
        self.hf_model_name = os.getenv(
            "HF_EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )
        
        # Determine provider
        if provider:
            self.provider = provider
        elif self.openai_api_key:
            self.provider = EmbeddingProvider.OPENAI
            logger.info(f"Using OpenAI embeddings: {self.openai_model}")
        else:
            self.provider = EmbeddingProvider.HUGGINGFACE
            logger.info(f"Using HuggingFace embeddings: {self.hf_model_name}")
        
        # Initialize HuggingFace model if needed
        self.hf_model = None
        if self.provider == EmbeddingProvider.HUGGINGFACE:
            self._init_huggingface_model()
        
        # Embedding dimensions
        self.embedding_dimension = self._get_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dimension}")

    def _init_huggingface_model(self):
        """Initialize HuggingFace sentence-transformers model."""
        try:
            logger.info(f"Loading HuggingFace model: {self.hf_model_name}")
            self.hf_model = SentenceTransformer(self.hf_model_name)
            logger.info("HuggingFace model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {str(e)}")
            raise

    def _get_embedding_dimension(self) -> int:
        """Get embedding dimension based on provider."""
        if self.provider == EmbeddingProvider.OPENAI:
            # OpenAI dimensions
            model_dimensions = {
                'text-embedding-3-large': 3072,
                'text-embedding-3-small': 1536,
                'text-embedding-ada-002': 1536
            }
            return model_dimensions.get(self.openai_model, 3072)
        
        elif self.provider == EmbeddingProvider.HUGGINGFACE:
            # Get dimension from model
            if self.hf_model:
                return self.hf_model.get_sentence_embedding_dimension()
            return 768  # Default for multilingual models
        
        else:
            return 768  # Default

    # ==================== PHASE 4: EMBEDDING GENERATION ====================

    async def generate_embedding(
        self,
        text: str,
        max_retries: int = 3
    ) -> List[float]:
        """
        Generate embedding vector for text.
        
        Phase 4: Single text embedding with retry logic
        
        Args:
            text: Text to embed
            max_retries: Maximum number of retry attempts
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            RuntimeError: If embedding generation fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return self._get_zero_embedding()
        
        # Truncate text if too long (safe limit for OpenAI text-embedding-3-large)
        text = self._truncate_text(text, max_tokens=7000)
        
        # Route to appropriate provider
        if self.provider == EmbeddingProvider.OPENAI:
            for attempt in range(max_retries):
                try:
                    return await self._generate_openai_embedding(text)
                except Exception as e:
                    logger.warning(f"OpenAI attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        logger.error("All OpenAI attempts failed. Falling back to HuggingFace.")
                        return await self._generate_huggingface_embedding(text)
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        elif self.provider == EmbeddingProvider.HUGGINGFACE:
            return await self._generate_huggingface_embedding(text)
        
        else:
            return await self._generate_local_embedding(text)

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Phase 4: Batch processing for efficiency
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}, size: {len(batch)}")
            
            if self.provider == EmbeddingProvider.OPENAI:
                # OpenAI supports batch API calls
                try:
                    batch_embeddings = await self._generate_openai_batch(batch)
                    embeddings.extend(batch_embeddings)
                except Exception as e:
                    logger.error(f"Batch OpenAI failed: {str(e)}. Processing individually.")
                    # Fallback to individual processing
                    batch_embeddings = await asyncio.gather(
                        *[self.generate_embedding(text) for text in batch],
                        return_exceptions=True
                    )
                    for j, embedding in enumerate(batch_embeddings):
                        if isinstance(embedding, Exception):
                            logger.error(f"Failed to embed text at index {i + j}")
                            embeddings.append(self._get_zero_embedding())
                        else:
                            embeddings.append(embedding)
            
            else:
                # HuggingFace batch processing
                batch_embeddings = await self._generate_huggingface_batch(batch)
                embeddings.extend(batch_embeddings)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings

    # ==================== OPENAI PROVIDER ====================

    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": text,
            "model": self.openai_model
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.openai_base_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                response_text = response.text
                
                # Handle specific token limit errors
                if response.status_code == 400 and "maximum context length" in response_text:
                    # Token limit exceeded - truncate more aggressively and retry once
                    logger.error(f"Token limit exceeded. Text length: {len(text)} chars, Error: {response_text}")
                    
                    # Try even more conservative truncation
                    retry_text = self._truncate_text(text, 5000)  # Even smaller limit
                    logger.warning(f"Retrying with more aggressive truncation: {len(retry_text)} chars")
                    
                    # Avoid infinite recursion by checking if text is already very small
                    if len(retry_text) < 1000:  
                        raise RuntimeError(f"Text too long even after aggressive truncation: {response_text}")
                    
                    # Retry one time with smaller truncation
                    return await self._generate_openai_embedding(retry_text)
                
                raise RuntimeError(f"OpenAI API error: {response.status_code} - {response_text}")
            
            data = response.json()
            embedding = data["data"][0]["embedding"]
            
            return embedding

    async def _generate_openai_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using OpenAI batch API.
        
        Args:
            texts: List of texts
            
        Returns:
            List of embedding vectors
        """
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": texts,
            "model": self.openai_model
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.openai_base_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"OpenAI batch API error: {response.status_code}")
            
            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]
            
            return embeddings

    # ==================== HUGGINGFACE PROVIDER ====================

    async def _generate_huggingface_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using HuggingFace sentence-transformers.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._generate_hf_sync,
            text
        )

    def _generate_hf_sync(self, text: str) -> List[float]:
        """Synchronous HuggingFace embedding generation."""
        if not self.hf_model:
            self._init_huggingface_model()
        
        embedding = self.hf_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def _generate_huggingface_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using HuggingFace.
        
        Args:
            texts: List of texts
            
        Returns:
            List of embedding vectors
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._generate_hf_batch_sync,
            texts
        )

    def _generate_hf_batch_sync(self, texts: List[str]) -> List[List[float]]:
        """Synchronous HuggingFace batch embedding generation."""
        if not self.hf_model:
            self._init_huggingface_model()
        
        embeddings = self.hf_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True
        )
        return [emb.tolist() for emb in embeddings]

    # ==================== LOCAL FALLBACK ====================

    async def _generate_local_embedding(self, text: str) -> List[float]:
        """
        Generate simple local embedding as fallback.
        
        This is a basic TF-IDF-like approach for demonstration.
        In production, use sentence-transformers.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Simple hash-based embedding for fallback
        words = text.lower().split()
        
        # Create a simple frequency-based vector
        embedding = np.zeros(self.embedding_dimension)
        
        for i, word in enumerate(words[:1000]):  # Limit to first 1000 words
            # Use hash to map words to embedding dimensions
            for j in range(3):  # Multiple positions per word
                idx = (hash(word + str(j)) % self.embedding_dimension)
                embedding[idx] += 1.0 / (i + 1)  # Position-weighted
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding.tolist()

    # ==================== UTILITY METHODS ====================

    def _get_zero_embedding(self) -> List[float]:
        """
        Get zero embedding vector.
        
        Returns:
            Zero vector of correct dimension
        """
        return [0.0] * self.embedding_dimension

    def _truncate_text(self, text: str, max_tokens: int = 7000) -> str:
        """
        Truncate text to maximum token count with accurate counting.
        
        OpenAI text-embedding-3-large has 8192 token limit.
        We use 7000 tokens as buffer to account for model overhead.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens (default: 7000 for safety)
            
        Returns:
            Truncated text
        """
        # Use accurate token counting if tiktoken is available
        if TIKTOKEN_AVAILABLE and self.provider == EmbeddingProvider.OPENAI:
            try:
                return self._truncate_with_tiktoken(text, max_tokens)
            except Exception as e:
                logger.warning(f"Tiktoken truncation failed: {e}. Using fallback method.")
        
        # Fallback to character-based estimation
        return self._truncate_with_chars(text, max_tokens)
    
    def _truncate_with_tiktoken(self, text: str, max_tokens: int) -> str:
        """Truncate using accurate tiktoken tokenizer."""
        encoding = tiktoken.encoding_for_model("text-embedding-3-large")
        
        # Get tokens and truncate if needed
        tokens = encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        # Truncate tokens
        truncated_tokens = tokens[:max_tokens]
        
        # Convert back to text
        truncated_text = encoding.decode(truncated_tokens)
        
        logger.info(f"Tiktoken truncation: {len(tokens)} -> {len(truncated_tokens)} tokens")
        return truncated_text
    
    def _truncate_with_chars(self, text: str, max_tokens: int) -> str:
        """Fallback character-based truncation."""
        # Conservative token estimation:
        # Arabic text: ~2-3 chars per token
        # English text: ~4 chars per token  
        # Mixed content: ~3 chars per token (conservative estimate)
        
        # Use conservative multiplier of 2.5 chars per token for safety
        max_chars = int(max_tokens * 2.5)
        
        if len(text) <= max_chars:
            return text
        
        # Truncate at word boundary
        truncated = text[:max_chars]
        last_space = truncated.rfind(' ')
        
        if last_space > 0 and last_space > max_chars * 0.8:  # If space is close enough
            truncated = truncated[:last_space]
        else:
            # Fallback: truncate at sentence boundary
            last_period = truncated.rfind('.')
            if last_period > 0 and last_period > max_chars * 0.7:
                truncated = truncated[:last_period + 1]
        
        logger.info(f"Char-based truncation: {len(text)} -> {len(truncated)} chars (est. tokens: {len(truncated) / 2.5:.0f})")
        return truncated

    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        if len(embedding1) != len(embedding2):
            logger.error("Embedding dimensions don't match")
            return 0.0
        
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Normalize to 0-1 range
        return max(0.0, min(1.0, (similarity + 1) / 2))

    async def check_api_status(self) -> bool:
        """
        Check if embedding service is accessible.
        
        Returns:
            True if service is accessible, False otherwise
        """
        try:
            test_embedding = await self.generate_embedding("test")
            return len(test_embedding) > 0
        except Exception as e:
            logger.error(f"Embedding service check failed: {str(e)}")
            return False

