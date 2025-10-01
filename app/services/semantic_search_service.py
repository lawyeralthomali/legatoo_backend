"""
Semantic Search Service for hybrid vector + keyword search.

This service implements high-performance semantic search combining
vector similarity with traditional keyword filtering for legal documents.
"""

import logging
import time
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.legal_document_repository import LegalDocumentRepository
from .embedding_service import EmbeddingService
from ..models.legal_document2 import LegalDocumentChunk, LegalDocument

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """Service for semantic search operations."""

    def __init__(
        self,
        repository: LegalDocumentRepository,
        embedding_service: EmbeddingService
    ):
        """
        Initialize semantic search service.
        
        Args:
            repository: Legal document repository
            embedding_service: Embedding service for vector operations
        """
        self.repository = repository
        self.embedding_service = embedding_service

    async def search(
        self,
        query: str,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        article_number: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.5
    ) -> Tuple[List[Dict], float]:
        """
        Perform hybrid semantic + keyword search.
        
        Args:
            query: Search query text
            document_type: Filter by document type
            language: Filter by language
            article_number: Filter by article number
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            Tuple of (search results, query time in ms)
        """
        start_time = time.time()
        
        try:
            # Step 1: Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Step 2: Apply keyword filters to narrow down search space
            filtered_chunks = await self.repository.search_chunks_by_filters(
                document_type=document_type,
                language=language,
                article_number=article_number,
                limit=1000  # Pre-filter to reasonable size
            )
            
            logger.info(f"Filtered to {len(filtered_chunks)} chunks before vector search")
            
            # Step 3: Calculate similarity scores for filtered chunks
            results = []
            
            for chunk in filtered_chunks:
                # Skip chunks without embeddings
                if not chunk.embedding or len(chunk.embedding) == 0:
                    continue
                
                # Calculate cosine similarity
                similarity = self.embedding_service.calculate_similarity(
                    query_embedding,
                    chunk.embedding
                )
                
                # Filter by threshold
                if similarity >= similarity_threshold:
                    results.append({
                        'chunk': chunk,
                        'similarity_score': similarity,
                        'highlights': self._extract_highlights(query, chunk.content)
                    })
            
            # Step 4: Sort by similarity and limit results
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            results = results[:limit]
            
            query_time = (time.time() - start_time) * 1000  # Convert to ms
            logger.info(f"Search completed in {query_time:.2f}ms, found {len(results)} results")
            
            return results, query_time
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            query_time = (time.time() - start_time) * 1000
            return [], query_time

    async def search_similar_chunks(
        self,
        chunk_id: int,
        limit: int = 5,
        same_document: bool = False
    ) -> List[Dict]:
        """
        Find similar chunks to a given chunk.
        
        Args:
            chunk_id: Source chunk ID
            limit: Maximum number of results
            same_document: Only search within same document
            
        Returns:
            List of similar chunks with scores
        """
        # Get source chunk
        source_chunk = await self.repository.get_chunk_by_id(chunk_id)
        if not source_chunk or not source_chunk.embedding:
            logger.warning(f"Chunk {chunk_id} not found or has no embedding")
            return []
        
        # Get all chunks to compare
        if same_document:
            candidate_chunks = await self.repository.get_chunks_by_document(
                source_chunk.document_id,
                limit=1000
            )
        else:
            # This is simplified - in production, use vector DB for efficiency
            # For now, we'll get chunks from all documents (limited)
            candidate_chunks = await self._get_all_chunks_sample(limit=500)
        
        # Calculate similarities
        results = []
        for chunk in candidate_chunks:
            # Skip self and chunks without embeddings
            if chunk.id == chunk_id or not chunk.embedding:
                continue
            
            similarity = self.embedding_service.calculate_similarity(
                source_chunk.embedding,
                chunk.embedding
            )
            
            results.append({
                'chunk': chunk,
                'similarity_score': similarity
            })
        
        # Sort and limit
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:limit]

    async def _get_all_chunks_sample(self, limit: int) -> List[LegalDocumentChunk]:
        """
        Get sample of chunks from all documents.
        
        This is a simplified implementation. In production, use proper vector DB.
        
        Args:
            limit: Maximum number of chunks
            
        Returns:
            List of chunks
        """
        # This would ideally query vector DB directly
        # For now, we'll get from recent documents
        documents, _ = await self.repository.get_documents(limit=50)
        
        chunks = []
        for doc in documents:
            doc_chunks = await self.repository.get_chunks_by_document(doc.id, limit=10)
            chunks.extend(doc_chunks)
            
            if len(chunks) >= limit:
                break
        
        return chunks[:limit]

    def _extract_highlights(
        self,
        query: str,
        content: str,
        context_words: int = 5
    ) -> List[str]:
        """
        Extract highlighted snippets matching query terms.
        
        Args:
            query: Search query
            content: Content to search in
            context_words: Number of words before/after match
            
        Returns:
            List of highlighted snippets
        """
        highlights = []
        
        # Extract query terms
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        # Find matches
        for term in query_terms:
            if len(term) < 3:  # Skip short terms
                continue
            
            # Find term positions
            start = 0
            while True:
                pos = content_lower.find(term, start)
                if pos == -1:
                    break
                
                # Extract context
                words = content.split()
                word_positions = []
                current_pos = 0
                
                for i, word in enumerate(words):
                    if current_pos <= pos < current_pos + len(word):
                        # Found the word
                        start_idx = max(0, i - context_words)
                        end_idx = min(len(words), i + context_words + 1)
                        snippet = ' '.join(words[start_idx:end_idx])
                        
                        if snippet not in highlights:
                            highlights.append(snippet)
                        break
                    
                    current_pos += len(word) + 1  # +1 for space
                
                start = pos + len(term)
                
                if len(highlights) >= 3:  # Limit highlights
                    break
            
            if len(highlights) >= 3:
                break
        
        return highlights

    async def rerank_results(
        self,
        results: List[Dict],
        boost_recent: bool = True,
        boost_articles: bool = True
    ) -> List[Dict]:
        """
        Re-rank search results with additional signals.
        
        Args:
            results: Initial search results
            boost_recent: Boost recently uploaded documents
            boost_articles: Boost chunks with article numbers
            
        Returns:
            Re-ranked results
        """
        import datetime
        
        for result in results:
            chunk = result['chunk']
            base_score = result['similarity_score']
            
            # Start with base similarity
            final_score = base_score
            
            # Boost for article numbers
            if boost_articles and chunk.article_number:
                final_score *= 1.1
            
            # Boost for recent documents
            if boost_recent and hasattr(chunk, 'document') and chunk.document:
                days_old = (datetime.datetime.now(datetime.timezone.utc) - chunk.document.created_at).days
                if days_old < 30:
                    final_score *= 1.05
            
            result['final_score'] = final_score
        
        # Re-sort by final score
        results.sort(key=lambda x: x.get('final_score', x['similarity_score']), reverse=True)
        
        return results

    async def get_search_suggestions(
        self,
        partial_query: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get search suggestions based on partial query.
        
        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested queries
        """
        # This is a simplified implementation
        # In production, maintain a query log and suggest popular queries
        
        suggestions = []
        
        # Common legal queries (Arabic)
        common_arabic = [
            "حقوق العامل",
            "إنهاء العقد",
            "فترة التجربة",
            "الإجازات السنوية",
            "ساعات العمل",
            "مكافأة نهاية الخدمة",
            "عقد العمل",
            "الفصل التعسفي"
        ]
        
        # Common legal queries (English)
        common_english = [
            "employee rights",
            "contract termination",
            "probation period",
            "annual leave",
            "working hours",
            "end of service",
            "employment contract",
            "wrongful termination"
        ]
        
        # Combine and filter
        all_suggestions = common_arabic + common_english
        partial_lower = partial_query.lower()
        
        for suggestion in all_suggestions:
            if partial_lower in suggestion.lower():
                suggestions.append(suggestion)
                
                if len(suggestions) >= limit:
                    break
        
        return suggestions

