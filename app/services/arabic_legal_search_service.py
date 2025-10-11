import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from ..models.legal_knowledge import (
    KnowledgeChunk, LawSource, LawArticle, LegalCase,
    LawBranch, LawChapter
)
from .arabic_legal_embedding_service import ArabicLegalEmbeddingService

logger = logging.getLogger(__name__)


class ArabicLegalSearchService:
    """
    خدمة البحث الدلالي المتخصصة للنصوص القانونية العربية
    
    Features:
    - Arabic-specialized BERT models
    - FAISS fast indexing
    - Sub-second search times
    - Better accuracy for legal terminology
    - Optimized result enrichment
    """
    
    def __init__(
        self,
        db: AsyncSession,
        model_name: str = 'sts-arabert',
        use_faiss: bool = True
    ):
        """
        Initialize Arabic Legal Search Service.
        
        Args:
            db: Async database session
            model_name: Model to use (default: 'sts-arabert' - specialized for semantic similarity)
            use_faiss: Whether to use FAISS for fast search
        """
        self.db = db
        self.embedding_service = ArabicLegalEmbeddingService(
            db=db,
            model_name=model_name,
            use_faiss=use_faiss
        )
        
        # Performance settings
        self.cache_enabled = True
        self._query_cache: Dict[str, List[Dict]] = {}
        self._cache_max_size = 200  # Increased cache
        
        # Boost factors
        self.VERIFIED_BOOST = 1.15  # +15% for verified
        self.RECENCY_BOOST = 1.10   # +10% for recent
        self.RECENCY_DAYS = 90      # Consider recent if < 90 days
        
        logger.info(f"🔍 Arabic Legal Search Service initialized")
        logger.info(f"   Model: {model_name}")
        logger.info(f"   FAISS: {'Enabled' if use_faiss else 'Disabled'}")
    
    async def initialize(self) -> None:
        """Initialize the service (load model, build index)."""
        logger.info("🚀 Initializing Arabic Legal Search Service...")
        
        # Load model
        self.embedding_service.initialize_model()
        
        # Build FAISS index if enabled
        if self.embedding_service.use_faiss:
            await self.embedding_service.build_faiss_index()
        
        logger.info("✅ Arabic Legal Search Service ready")
    
    def _calculate_relevance_score(
        self,
        base_similarity: float,
        chunk: KnowledgeChunk,
        apply_boosts: bool = True
    ) -> float:
        """
        Calculate final relevance score with boost factors.
        
        Args:
            base_similarity: Base similarity score
            chunk: Knowledge chunk
            apply_boosts: Whether to apply boost factors
            
        Returns:
            Final relevance score
        """
        if not apply_boosts:
            return base_similarity
        
        score = base_similarity
        
        # Verified content boost
        if chunk.verified_by_admin:
            score *= self.VERIFIED_BOOST
        
        # Recency boost
        if hasattr(chunk, 'created_at') and chunk.created_at:
            days_old = (datetime.utcnow() - chunk.created_at).days
            if days_old < self.RECENCY_DAYS:
                score *= self.RECENCY_BOOST
        
        # Cap at 1.0
        return min(score, 1.0)
    
    async def find_similar_laws(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        use_fast_search: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find similar laws using Arabic-optimized search.
        
        Args:
            query: Search query
            top_k: Number of results
            threshold: Minimum similarity threshold
            filters: Optional filters (jurisdiction, law_source_id)
            use_fast_search: Use FAISS if available
            
        Returns:
            List of similar laws with metadata
        """
        try:
            logger.info(f"🔍 Searching for similar laws: '{query[:50]}...'")
            
            # Check cache
            cache_key = f"laws_{query}_{top_k}_{threshold}_{str(filters)}"
            if self.cache_enabled and cache_key in self._query_cache:
                logger.info(f"📦 Cache hit!")
                return self._query_cache[cache_key]
            
            # Use FAISS fast search if available
            if use_fast_search and self.embedding_service.use_faiss and self.embedding_service.faiss_index:
                results = await self._fast_search_laws(query, top_k, threshold, filters)
            else:
                results = await self._standard_search_laws(query, top_k, threshold, filters)
            
            # Cache results
            if self.cache_enabled and len(self._query_cache) < self._cache_max_size:
                self._query_cache[cache_key] = results
            
            logger.info(f"✅ Found {len(results)} similar laws")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            return []
    
    async def _fast_search_laws(
        self,
        query: str,
        top_k: int,
        threshold: float,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fast search using FAISS index.
        
        Args:
            query: Search query
            top_k: Number of results
            threshold: Similarity threshold
            filters: Optional filters
            
        Returns:
            List of enriched results
        """
        logger.info("⚡ Using FAISS fast search")
        
        # Get top candidates from FAISS (get more for filtering)
        candidates_k = top_k * 3 if filters else top_k
        faiss_results = await self.embedding_service.search_similar_fast(
            query=query,
            top_k=candidates_k
        )
        
        # Get chunk IDs
        chunk_ids = [r['chunk_id'] for r in faiss_results]
        
        # Fetch chunks from database
        query_builder = select(KnowledgeChunk).where(
            KnowledgeChunk.id.in_(chunk_ids)
        )
        
        # Apply filters
        if filters:
            if 'law_source_id' in filters:
                query_builder = query_builder.where(
                    KnowledgeChunk.law_source_id == filters['law_source_id']
                )
            if 'jurisdiction' in filters:
                query_builder = query_builder.join(
                    LawSource,
                    KnowledgeChunk.law_source_id == LawSource.id
                ).where(LawSource.jurisdiction == filters['jurisdiction'])
        
        result = await self.db.execute(query_builder)
        chunks = {chunk.id: chunk for chunk in result.scalars().all()}
        
        # Build results with enrichment
        results = []
        for faiss_result in faiss_results:
            chunk_id = faiss_result['chunk_id']
            base_similarity = faiss_result['similarity']
            
            if chunk_id in chunks:
                chunk = chunks[chunk_id]
                
                # Apply boost factors
                similarity = self._calculate_relevance_score(
                    base_similarity,
                    chunk,
                    apply_boosts=True
                )
                
                # Check threshold
                if similarity >= threshold:
                    enriched = await self._enrich_law_result(chunk, similarity)
                    results.append(enriched)
                    
                    if len(results) >= top_k:
                        break
        
        return results
    
    async def _execute_standard_search_query(
        self,
        query_vector: np.ndarray,
        source_type: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Unified standard search logic for both laws and cases.
        
        Args:
            query_vector: Pre-computed query embedding vector
            source_type: Type of source ('law' or 'case')
            filters: Optional filters dictionary
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of enriched search results
        """
        logger.info(f"🔍 Using standard search for {source_type}s")
        
        # Build base query based on source type
        if source_type == 'law':
            query_builder = select(KnowledgeChunk).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != '',
                    KnowledgeChunk.law_source_id.isnot(None)
                )
            )
            
            # Apply law-specific filters
            if filters:
                if 'law_source_id' in filters:
                    query_builder = query_builder.where(
                        KnowledgeChunk.law_source_id == filters['law_source_id']
                    )
                if 'jurisdiction' in filters:
                    query_builder = query_builder.join(
                        LawSource,
                        KnowledgeChunk.law_source_id == LawSource.id
                    ).where(LawSource.jurisdiction == filters['jurisdiction'])
                    
        elif source_type == 'case':
            query_builder = select(KnowledgeChunk).where(
                and_(
                    KnowledgeChunk.embedding_vector.isnot(None),
                    KnowledgeChunk.embedding_vector != '',
                    KnowledgeChunk.case_id.isnot(None)
                )
            )
            
            # Apply case-specific filters
            if filters:
                if 'case_id' in filters:
                    query_builder = query_builder.where(
                        KnowledgeChunk.case_id == filters['case_id']
                    )
                if 'jurisdiction' in filters or 'case_type' in filters or 'court_level' in filters:
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
        else:
            raise ValueError(f"Invalid source_type: {source_type}. Must be 'law' or 'case'")
        
        # Execute query
        result = await self.db.execute(query_builder)
        chunks = result.scalars().all()
        
        logger.info(f"📊 Found {len(chunks)} {source_type} chunks to search")
        
        # Calculate similarities
        results = []
        for chunk in chunks:
            try:
                # Deserialize embedding vector from JSON string (SQLite compatible)
                chunk_embedding = np.array(json.loads(chunk.embedding_vector))
                
                # Calculate cosine similarity
                base_similarity = self.embedding_service.cosine_similarity(
                    query_vector,
                    chunk_embedding
                )
                
                # Apply boost factors
                similarity = self._calculate_relevance_score(
                    base_similarity,
                    chunk,
                    apply_boosts=True
                )
                
                # Filter by threshold
                if similarity >= threshold:
                    # Enrich based on source type
                    if source_type == 'law':
                        enriched = await self._enrich_law_result(chunk, similarity)
                    else:
                        enriched = await self._enrich_case_result(chunk, similarity)
                    
                    results.append(enriched)
                    
            except Exception as e:
                logger.warning(f"⚠️  Failed to process chunk {chunk.id}: {str(e)}")
                continue
        
        # Sort by similarity (descending) and limit to top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:top_k]
        
        logger.info(f"✅ Found {len(results)} similar {source_type}s above threshold")
        
        return results
    
    async def _standard_search_laws(
        self,
        query: str,
        top_k: int,
        threshold: float,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Standard search for laws (wrapper for unified search logic).
        
        Args:
            query: Search query
            top_k: Number of results
            threshold: Similarity threshold
            filters: Optional filters
            
        Returns:
            List of enriched law results
        """
        # Generate query embedding
        query_embedding = self.embedding_service.encode_text(query)
        
        # Use unified search logic
        return await self._execute_standard_search_query(
            query_vector=query_embedding,
            source_type='law',
            filters=filters,
            top_k=top_k,
            threshold=threshold
        )
    
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
            law_query = select(LawSource).where(LawSource.id == chunk.law_source_id)
            law_result = await self.db.execute(law_query)
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
        
        # Add branch metadata
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
        
        # Add chapter metadata
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
    
    async def find_similar_cases(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar legal cases (wrapper for unified search logic).
        
        Args:
            query: Search query
            top_k: Number of results
            threshold: Similarity threshold
            filters: Optional filters
            
        Returns:
            List of similar cases
        """
        try:
            logger.info(f"🔍 Searching for similar cases: '{query[:50]}...'")
            
            # Generate query embedding
            query_embedding = self.embedding_service.encode_text(query)
            
            # Use unified search logic
            results = await self._execute_standard_search_query(
                query_vector=query_embedding,
                source_type='case',
                filters=filters,
                top_k=top_k,
                threshold=threshold
            )
            
            logger.info(f"✅ Found {len(results)} similar cases")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Case search failed: {str(e)}")
            return []
    
    async def _enrich_case_result(
        self,
        chunk: KnowledgeChunk,
        similarity: float
    ) -> Dict[str, Any]:
        """Enrich case search result with metadata."""
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
    
    async def hybrid_search(
        self,
        query: str,
        search_types: List[str] = ['laws', 'cases'],
        top_k: int = 5,
        threshold: float = 0.6,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Hybrid search across multiple document types.
        
        Args:
            query: Search query
            search_types: Types to search ['laws', 'cases', 'all']
            top_k: Number of results per type
            threshold: Similarity threshold
            filters: Optional filters
            
        Returns:
            Dictionary with results from each type
        """
        try:
            logger.info(f"🔍 Hybrid search: '{query[:50]}...' across {search_types}")
            
            results = {
                'query': query,
                'search_types': search_types,
                'total_results': 0
            }
            
            # Search laws
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
                results['total_results'] += len(law_results)
            
            # Search cases
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
                results['total_results'] += len(case_results)
            
            logger.info(f"✅ Hybrid search complete: {results['total_results']} total results")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {str(e)}")
            return {
                'query': query,
                'error': str(e),
                'total_results': 0
            }
    
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
            
            # Search in case titles if LegalCase exists
            try:
                case_query = select(LegalCase.title).where(
                    LegalCase.title.ilike(f"%{partial_query}%")
                ).limit(limit)
                
                case_result = await self.db.execute(case_query)
                case_titles = case_result.scalars().all()
                suggestions.extend(case_titles)
            except:
                pass  # LegalCase might not have title field
            
            # Remove duplicates and limit
            suggestions = list(set(suggestions))[:limit]
            
            logger.info(f"✅ Found {len(suggestions)} suggestions")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Failed to get suggestions: {str(e)}")
            return []
    
    def clear_cache(self) -> None:
        """Clear query cache."""
        self._query_cache.clear()
        self.embedding_service.clear_cache()
        logger.info("🗑️  All caches cleared")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get search service statistics."""
        # Count chunks
        total_query = select(func.count(KnowledgeChunk.id)).where(
            and_(
                KnowledgeChunk.embedding_vector.isnot(None),
                KnowledgeChunk.embedding_vector != ''
            )
        )
        total_result = await self.db.execute(total_query)
        total_chunks = total_result.scalar() or 0
        
        # Count law chunks
        law_query = select(func.count(KnowledgeChunk.id)).where(
            and_(
                KnowledgeChunk.embedding_vector.isnot(None),
                KnowledgeChunk.embedding_vector != '',
                KnowledgeChunk.law_source_id.isnot(None)
            )
        )
        law_result = await self.db.execute(law_query)
        law_chunks = law_result.scalar() or 0
        
        # Count case chunks
        case_query = select(func.count(KnowledgeChunk.id)).where(
            and_(
                KnowledgeChunk.embedding_vector.isnot(None),
                KnowledgeChunk.embedding_vector != '',
                KnowledgeChunk.case_id.isnot(None)
            )
        )
        case_result = await self.db.execute(case_query)
        case_chunks = case_result.scalar() or 0
        
        # Get model info
        model_info = self.embedding_service.get_model_info()
        
        return {
            'total_searchable_chunks': total_chunks,
            'law_chunks': law_chunks,
            'case_chunks': case_chunks,
            'query_cache_size': len(self._query_cache),
            'cache_enabled': self.cache_enabled,
            'model_info': model_info
        }

