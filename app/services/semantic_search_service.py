"""
Semantic Search Service - خدمة البحث الدلالي المتقدمة للنصوص القانونية العربية

This service provides advanced semantic search capabilities for legal documents,
enabling AI-powered legal analysis and intelligent document retrieval.
"""

import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from ..models.legal_knowledge import (
    KnowledgeChunk, LawSource, LawArticle, LegalCase, CaseSection, 
    KnowledgeDocument, LawBranch, LawChapter
)
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    خدمة البحث الدلالي المتقدمة للنصوص القانونية العربية.
    
    Features:
    - Semantic search for laws and legal articles
    - Semantic search for legal cases and precedents
    - Hybrid search across multiple document types
    - Relevance scoring and ranking
    - Filtering by jurisdiction, type, date, etc.
    - Result enrichment with metadata
    """
    
    def __init__(self, db: AsyncSession, model_name: str = 'default'):
        """
        Initialize the semantic search service.
        
        Args:
            db: Async database session
            model_name: Embedding model to use ('default', 'large', 'small')
        """
        self.db = db
        self.embedding_service = EmbeddingService(db, model_name=model_name)
        
        # Performance settings
        self.cache_enabled = True
        self._query_cache: Dict[str, List[Dict]] = {}
        self._cache_max_size = 100
    
    # ==================== SIMILARITY CALCULATION ====================
    
    def _cosine_similarity(
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
            Similarity score (0.0 to 1.0)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
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
    
    def _calculate_relevance_score(
        self,
        query_embedding: List[float],
        chunk: KnowledgeChunk,
        boost_factors: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate relevance score with optional boosting factors.
        
        Args:
            query_embedding: Query embedding vector
            chunk: Knowledge chunk to score
            boost_factors: Optional factors to boost relevance (e.g., recency, importance)
            
        Returns:
            Final relevance score
        """
        try:
            # Base similarity score
            chunk_embedding = json.loads(chunk.embedding_vector)
            base_score = self._cosine_similarity(query_embedding, chunk_embedding)
            
            # Apply boost factors if provided
            if boost_factors:
                # Verified content boost
                if boost_factors.get('verified_boost') and chunk.verified_by_admin:
                    base_score *= 1.1
                
                # Recency boost (if applicable)
                if boost_factors.get('recency_boost') and hasattr(chunk, 'created_at'):
                    days_old = (datetime.utcnow() - chunk.created_at).days
                    if days_old < 30:
                        base_score *= 1.05
            
            return min(base_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate relevance score: {str(e)}")
            return 0.0
    
    # ==================== LAWS SEARCH ====================
    
    async def find_similar_laws(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        يبحث عن القوانين والمواد القانونية المشابهة للاستعلام.
        
        Args:
            query: Search query text (Arabic or English)
            top_k: Number of top results to return
            threshold: Minimum similarity threshold (0.0-1.0)
            filters: Optional filters (jurisdiction, law_source_id, etc.)
            
        Returns:
            List of similar laws with metadata
        """
        try:
            logger.info(f"🔍 Searching for similar laws: '{query[:50]}...'")
            
            # Check cache
            cache_key = f"laws_{query}_{top_k}_{threshold}"
            if self.cache_enabled and cache_key in self._query_cache:
                logger.debug(f"📦 Using cached results")
                return self._query_cache[cache_key]
            
            # Generate query embedding
            query_embedding = self.embedding_service._encode_text(query)
            
            # Build query for law chunks
            query_builder = select(KnowledgeChunk).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != '',
                    KnowledgeChunk.law_source_id.isnot(None)  # Only law chunks
                )
            )
            
            # Apply filters
            if filters:
                if 'law_source_id' in filters:
                    query_builder = query_builder.where(
                        KnowledgeChunk.law_source_id == filters['law_source_id']
                    )
                if 'jurisdiction' in filters:
                    # Join with LawSource to filter by jurisdiction
                    query_builder = query_builder.join(
                        LawSource,
                        KnowledgeChunk.law_source_id == LawSource.id
                    ).where(LawSource.jurisdiction == filters['jurisdiction'])
            
            result = await self.db.execute(query_builder)
            chunks = result.scalars().all()
            
            logger.info(f"📊 Found {len(chunks)} law chunks to search")
            
            if not chunks:
                return []
            
            # Calculate similarities
            results = []
            for chunk in chunks:
                try:
                    similarity = self._calculate_relevance_score(
                        query_embedding,
                        chunk,
                        boost_factors={'verified_boost': True}
                    )
                    
                    if similarity >= threshold:
                        # Enrich with metadata
                        enriched_result = await self._enrich_law_result(chunk, similarity)
                        results.append(enriched_result)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process chunk {chunk.id}: {str(e)}")
                    continue
            
            # Sort by similarity and take top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            results = results[:top_k]
            
            # Cache results
            if self.cache_enabled and len(self._query_cache) < self._cache_max_size:
                self._query_cache[cache_key] = results
            
            logger.info(f"✅ Found {len(results)} similar laws above threshold {threshold}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to search for similar laws: {str(e)}")
            return []
    
    async def _enrich_law_result(
        self,
        chunk: KnowledgeChunk,
        similarity: float
    ) -> Dict[str, Any]:
        """
        Enrich law search result with metadata.
        
        Args:
            chunk: Knowledge chunk
            similarity: Similarity score
            
        Returns:
            Enriched result dictionary
        """
        result = {
            'chunk_id': chunk.id,
            'content': chunk.content,
            'similarity': round(similarity, 4),
            'source_type': 'law',
            'chunk_index': chunk.chunk_index,
            'tokens_count': chunk.tokens_count,
            'verified': chunk.verified_by_admin
        }
        
        # Add law source metadata
        if chunk.law_source_id:
            law_source_query = select(LawSource).where(LawSource.id == chunk.law_source_id)
            law_result = await self.db.execute(law_source_query)
            law_source = law_result.scalar_one_or_none()
            
            if law_source:
                result['law_metadata'] = {
                    'law_id': law_source.id,
                    'law_name': law_source.name,
                    'law_type': law_source.type,
                    'jurisdiction': law_source.jurisdiction,
                    'issue_date': law_source.issue_date.isoformat() if law_source.issue_date else None
                }
        
        # Add article metadata
        if chunk.article_id:
            article_query = select(LawArticle).where(LawArticle.id == chunk.article_id)
            article_result = await self.db.execute(article_query)
            article = article_result.scalar_one_or_none()
            
            if article:
                result['article_metadata'] = {
                    'article_id': article.id,
                    'article_number': article.article_number,
                    'title': article.title,
                    'keywords': article.keywords
                }
        
        # Add branch/chapter metadata
        if chunk.branch_id:
            branch_query = select(LawBranch).where(LawBranch.id == chunk.branch_id)
            branch_result = await self.db.execute(branch_query)
            branch = branch_result.scalar_one_or_none()
            
            if branch:
                result['branch_metadata'] = {
                    'branch_id': branch.id,
                    'branch_number': branch.branch_number,
                    'branch_name': branch.branch_name
                }
        
        if chunk.chapter_id:
            chapter_query = select(LawChapter).where(LawChapter.id == chunk.chapter_id)
            chapter_result = await self.db.execute(chapter_query)
            chapter = chapter_result.scalar_one_or_none()
            
            if chapter:
                result['chapter_metadata'] = {
                    'chapter_id': chapter.id,
                    'chapter_number': chapter.chapter_number,
                    'chapter_name': chapter.chapter_name
                }
        
        return result
    
    # ==================== CASES SEARCH ====================
    
    async def find_similar_cases(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        يبحث عن القضايا القانونية المشابهة للاستعلام.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            filters: Optional filters (jurisdiction, case_type, court_level, etc.)
            
        Returns:
            List of similar cases with metadata
        """
        try:
            logger.info(f"🔍 Searching for similar cases: '{query[:50]}...'")
            
            # Check cache
            cache_key = f"cases_{query}_{top_k}_{threshold}"
            if self.cache_enabled and cache_key in self._query_cache:
                logger.debug(f"📦 Using cached results")
                return self._query_cache[cache_key]
            
            # Generate query embedding
            query_embedding = self.embedding_service._encode_text(query)
            
            # Build query for case chunks
            query_builder = select(KnowledgeChunk).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != '',
                    KnowledgeChunk.case_id.isnot(None)  # Only case chunks
                )
            )
            
            # Apply filters
            if filters:
                if 'case_id' in filters:
                    query_builder = query_builder.where(
                        KnowledgeChunk.case_id == filters['case_id']
                    )
                if 'jurisdiction' in filters or 'case_type' in filters or 'court_level' in filters:
                    # Join with LegalCase to filter
                    query_builder = query_builder.join(
                        LegalCase,
                        KnowledgeChunk.case_id == LegalCase.id
                    )
                    if 'jurisdiction' in filters:
                        query_builder = query_builder.where(
                            LegalCase.jurisdiction == filters['jurisdiction']
                        )
                    if 'case_type' in filters:
                        query_builder = query_builder.where(
                            LegalCase.case_type == filters['case_type']
                        )
                    if 'court_level' in filters:
                        query_builder = query_builder.where(
                            LegalCase.court_level == filters['court_level']
                        )
            
            result = await self.db.execute(query_builder)
            chunks = result.scalars().all()
            
            logger.info(f"📊 Found {len(chunks)} case chunks to search")
            
            if not chunks:
                return []
            
            # Calculate similarities
            results = []
            for chunk in chunks:
                try:
                    similarity = self._calculate_relevance_score(
                        query_embedding,
                        chunk,
                        boost_factors={'verified_boost': True, 'recency_boost': True}
                    )
                    
                    if similarity >= threshold:
                        # Enrich with metadata
                        enriched_result = await self._enrich_case_result(chunk, similarity)
                        results.append(enriched_result)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process chunk {chunk.id}: {str(e)}")
                    continue
            
            # Sort by similarity and take top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            results = results[:top_k]
            
            # Cache results
            if self.cache_enabled and len(self._query_cache) < self._cache_max_size:
                self._query_cache[cache_key] = results
            
            logger.info(f"✅ Found {len(results)} similar cases above threshold {threshold}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to search for similar cases: {str(e)}")
            return []
    
    async def _enrich_case_result(
        self,
        chunk: KnowledgeChunk,
        similarity: float
    ) -> Dict[str, Any]:
        """
        Enrich case search result with metadata.
        
        Args:
            chunk: Knowledge chunk
            similarity: Similarity score
            
        Returns:
            Enriched result dictionary
        """
        result = {
            'chunk_id': chunk.id,
            'content': chunk.content,
            'similarity': round(similarity, 4),
            'source_type': 'case',
            'chunk_index': chunk.chunk_index,
            'tokens_count': chunk.tokens_count,
            'verified': chunk.verified_by_admin
        }
        
        # Add case metadata
        if chunk.case_id:
            case_query = select(LegalCase).where(LegalCase.id == chunk.case_id)
            case_result = await self.db.execute(case_query)
            case = case_result.scalar_one_or_none()
            
            if case:
                result['case_metadata'] = {
                    'case_id': case.id,
                    'case_number': case.case_number,
                    'title': case.title,
                    'jurisdiction': case.jurisdiction,
                    'court_name': case.court_name,
                    'decision_date': case.decision_date.isoformat() if case.decision_date else None,
                    'case_type': case.case_type,
                    'court_level': case.court_level,
                    'status': case.status
                }
        
        return result
    
    # ==================== HYBRID SEARCH ====================
    
    async def hybrid_search(
        self,
        query: str,
        search_types: List[str] = ['laws', 'cases'],
        top_k: int = 5,
        threshold: float = 0.6,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        بحث هجين عبر أنواع مختلفة من المستندات القانونية.
        
        Args:
            query: Search query text
            search_types: Types to search ['laws', 'cases', 'all']
            top_k: Number of results per type
            threshold: Minimum similarity threshold
            filters: Optional filters
            
        Returns:
            Dictionary with results from each type
        """
        try:
            logger.info(f"🔍 Hybrid search: '{query[:50]}...' across {search_types}")
            
            results = {
                'query': query,
                'search_types': search_types,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Search laws if requested
            if 'laws' in search_types or 'all' in search_types:
                law_results = await self.find_similar_laws(
                    query=query,
                    top_k=top_k,
                    threshold=threshold,
                    filters=filters
                )
                results['laws'] = {
                    'count': len(law_results),
                    'results': law_results
                }
            
            # Search cases if requested
            if 'cases' in search_types or 'all' in search_types:
                case_results = await self.find_similar_cases(
                    query=query,
                    top_k=top_k,
                    threshold=threshold,
                    filters=filters
                )
                results['cases'] = {
                    'count': len(case_results),
                    'results': case_results
                }
            
            # Calculate total results
            total_results = 0
            if 'laws' in results:
                total_results += results['laws']['count']
            if 'cases' in results:
                total_results += results['cases']['count']
            
            results['total_results'] = total_results
            
            logger.info(f"✅ Hybrid search completed: {total_results} total results")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to perform hybrid search: {str(e)}")
            return {
                'query': query,
                'error': str(e),
                'total_results': 0
            }
    
    # ==================== SEARCH SUGGESTIONS ====================
    
    async def get_search_suggestions(
        self,
        partial_query: str,
        limit: int = 5
    ) -> List[str]:
        """
        الحصول على اقتراحات بحث بناءً على استعلام جزئي.
        
        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List of search suggestions
        """
        try:
            logger.info(f"💡 Getting suggestions for: '{partial_query}'")
            
            suggestions = []
            
            # Search in law names
            law_query = select(LawSource.name).where(
                LawSource.name.ilike(f"%{partial_query}%")
            ).limit(limit)
            
            law_result = await self.db.execute(law_query)
            law_names = law_result.scalars().all()
            suggestions.extend(law_names)
            
            # Search in case titles
            case_query = select(LegalCase.title).where(
                LegalCase.title.ilike(f"%{partial_query}%")
            ).limit(limit)
            
            case_result = await self.db.execute(case_query)
            case_titles = case_result.scalars().all()
            suggestions.extend(case_titles)
            
            # Remove duplicates and limit
            suggestions = list(set(suggestions))[:limit]
            
            logger.info(f"✅ Found {len(suggestions)} suggestions")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Failed to get suggestions: {str(e)}")
            return []
    
    # ==================== UTILITY METHODS ====================
    
    def clear_cache(self) -> None:
        """Clear the query cache."""
        self._query_cache.clear()
        logger.info("🗑️ Query cache cleared")
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات البحث.
        
        Returns:
            Dictionary with search statistics
        """
        try:
            # Count chunks with embeddings
            total_chunks_query = select(func.count(KnowledgeChunk.id)).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != ''
                )
            )
            total_result = await self.db.execute(total_chunks_query)
            total_chunks = total_result.scalar() or 0
            
            # Count law chunks
            law_chunks_query = select(func.count(KnowledgeChunk.id)).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != '',
                    KnowledgeChunk.law_source_id.isnot(None)
                )
            )
            law_result = await self.db.execute(law_chunks_query)
            law_chunks = law_result.scalar() or 0
            
            # Count case chunks
            case_chunks_query = select(func.count(KnowledgeChunk.id)).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != '',
                    KnowledgeChunk.case_id.isnot(None)
                )
            )
            case_result = await self.db.execute(case_chunks_query)
            case_chunks = case_result.scalar() or 0
            
            return {
                'total_searchable_chunks': total_chunks,
                'law_chunks': law_chunks,
                'case_chunks': case_chunks,
                'cache_size': len(self._query_cache),
                'cache_enabled': self.cache_enabled
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {str(e)}")
            return {}