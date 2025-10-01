"""
Embedding Service for generating vector embeddings.

This service generates high-quality multilingual embeddings for semantic search,
supporting both Arabic and English legal documents.
"""

import logging
import os
from typing import List, Optional
import asyncio
import httpx
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        """Initialize embedding service with OpenAI API."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
        self.embedding_dimension = 3072  # text-embedding-3-large dimension
        self.base_url = "https://api.openai.com/v1/embeddings"
        
        # Fallback to local embedding if no API key
        self.use_local_fallback = not self.api_key
        
        if self.use_local_fallback:
            logger.warning("No OpenAI API key found. Using local fallback embeddings.")
        else:
            logger.info(f"Using OpenAI embedding model: {self.model}")

    async def generate_embedding(
        self,
        text: str,
        max_retries: int = 3
    ) -> List[float]:
        """
        Generate embedding vector for text.
        
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
        
        # Truncate text if too long (max 8191 tokens for OpenAI)
        text = self._truncate_text(text, max_tokens=8000)
        
        if self.use_local_fallback:
            return await self._generate_local_embedding(text)
        
        for attempt in range(max_retries):
            try:
                return await self._generate_openai_embedding(text)
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error("All embedding attempts failed. Using fallback.")
                    return await self._generate_local_embedding(text)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return self._get_zero_embedding()

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
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
            
            # Process batch concurrently
            batch_embeddings = await asyncio.gather(
                *[self.generate_embedding(text) for text in batch],
                return_exceptions=True
            )
            
            # Handle exceptions
            for j, embedding in enumerate(batch_embeddings):
                if isinstance(embedding, Exception):
                    logger.error(f"Failed to embed text at index {i + j}: {str(embedding)}")
                    embeddings.append(self._get_zero_embedding())
                else:
                    embeddings.append(embedding)
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings

    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": text,
            "model": self.model
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"OpenAI API error: {response.status_code} - {response.text}")
            
            data = response.json()
            embedding = data["data"][0]["embedding"]
            
            return embedding

    async def _generate_local_embedding(self, text: str) -> List[float]:
        """
        Generate simple local embedding as fallback.
        
        This is a basic TF-IDF-like approach for demonstration.
        In production, consider using sentence-transformers or similar.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Simple hash-based embedding for fallback
        # This maintains consistent dimensions but is not semantically meaningful
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

    def _get_zero_embedding(self) -> List[float]:
        """
        Get zero embedding vector.
        
        Returns:
            Zero vector of correct dimension
        """
        return [0.0] * self.embedding_dimension

    def _truncate_text(self, text: str, max_tokens: int = 8000) -> str:
        """
        Truncate text to maximum token count.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum number of tokens
            
        Returns:
            Truncated text
        """
        # Rough approximation: 1 token ≈ 4 characters for English, ≈ 2 for Arabic
        max_chars = max_tokens * 3
        
        if len(text) <= max_chars:
            return text
        
        # Truncate at word boundary
        truncated = text[:max_chars]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            truncated = truncated[:last_space]
        
        logger.info(f"Truncated text from {len(text)} to {len(truncated)} characters")
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
        Check if OpenAI API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        if self.use_local_fallback:
            return False
        
        try:
            test_embedding = await self._generate_openai_embedding("test")
            return len(test_embedding) > 0
        except Exception as e:
            logger.error(f"API status check failed: {str(e)}")
            return False

