"""
Semantic Search Service for Law Documents

Simplified version that works with LawDocument and LawChunk models only.
Provides fast semantic search capabilities using pre-computed embeddings.
"""

import logging
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from ...models.documnets import LawDocument, LawChunk
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """
    Semantic Search Service for law documents.
    
    Simplified to work with LawDocument and LawChunk models.
    """
    
    def __init__(self, db: AsyncSession, model_name: str = 'legal_optimized'):
        """
        Initialize Semantic Search Service.
        
        Args:
            db: Async database session
            model_name: Embedding model to use
        """
        self.db = db
        self.embedding_service = EmbeddingService(db, model_name=model_name)
        
        # Search settings
        self.default_top_k = 10
        self.default_threshold = 0.7
        
        # Cache for query results
        self._query_cache = {}
        self._cache_max_size = 100
        
        logger.info(f"🔍 Semantic Search Service initialized with model: {model_name}")
    
    async def search_similar_laws(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar law chunks using semantic similarity.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold (0.0 to 1.0)
            filters: Optional filters (document_id, jurisdiction, etc.)
            
        Returns:
            List of search results with similarity scores
        """
        try:
            logger.info(f"🔍 Searching for: '{query[:50]}...'")
            
            # Check cache
            cache_key = f"{query}_{top_k}_{threshold}_{str(filters)}"
            if cache_key in self._query_cache:
                logger.info("📦 Returning cached results")
                return self._query_cache[cache_key]
            
            # Initialize embedding service
            await self.embedding_service.initialize()
            
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Build query
            query_builder = (
                select(LawChunk, LawDocument)
                .join(LawDocument, LawChunk.document_id == LawDocument.id)
                .where(
                    and_(
                        LawChunk.embedding_vector.isnot(None),
                        LawChunk.embedding_vector != '',
                        LawChunk.is_processed == True
                    )
                )
            )
            
            # Apply filters
            if filters:
                if 'document_id' in filters:
                    query_builder = query_builder.where(
                        LawChunk.document_id == filters['document_id']
                    )
                if 'jurisdiction' in filters:
                    query_builder = query_builder.where(
                        LawDocument.jurisdiction.ilike(f"%{filters['jurisdiction']}%")
                    )
                if 'document_type' in filters:
                    query_builder = query_builder.where(
                        LawDocument.type == filters['document_type']
                    )
            
            # Execute query
            result = await self.db.execute(query_builder)
            rows = result.all()
            
            logger.info(f"📊 Found {len(rows)} chunks to search")
            
            # Calculate similarities
            results = []
            for chunk, document in rows:
                try:
                    chunk_embedding = json.loads(chunk.embedding_vector)
                    similarity = self.embedding_service.cosine_similarity(
                        query_embedding,
                        chunk_embedding
                    )
                    
                    if similarity >= threshold:
                        results.append({
                            'chunk_id': chunk.id,
                            'content': chunk.content,
                            'similarity': float(similarity),
                            'chunk_index': chunk.chunk_index,
                            'word_count': chunk.word_count,
                            'document': {
                                'id': document.id,
                                'name': document.name,
                                'type': document.type,
                                'jurisdiction': document.jurisdiction,
                                'uploaded_at': document.uploaded_at.isoformat() if document.uploaded_at else None
                            }
                        })
                        
                except Exception as e:
                    logger.warning(f"⚠️  Error processing chunk {chunk.id}: {str(e)}")
                    continue
            
            # Sort by similarity
            results.sort(key=lambda x: x['similarity'], reverse=True)
            results = results[:top_k]
            
            # Cache results
            if len(self._query_cache) < self._cache_max_size:
                self._query_cache[cache_key] = results
            
            logger.info(f"✅ Found {len(results)} results above threshold {threshold}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            return []
    
    async def find_similar_chunks(
        self,
        chunk_id: int,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find chunks similar to a given chunk.
        
        Args:
            chunk_id: ID of the source chunk
            top_k: Number of similar chunks to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of similar chunks
        """
        try:
            # Get source chunk
            chunk_query = select(LawChunk).where(LawChunk.id == chunk_id)
            chunk_result = await self.db.execute(chunk_query)
            source_chunk = chunk_result.scalar_one_or_none()
            
            if not source_chunk or not source_chunk.embedding_vector:
                logger.warning(f"⚠️  Chunk {chunk_id} not found or has no embedding")
                return []
            
            source_embedding = json.loads(source_chunk.embedding_vector)
            
            # Get all chunks with embeddings (excluding source)
            chunks_query = (
                select(LawChunk, LawDocument)
                .join(LawDocument, LawChunk.document_id == LawDocument.id)
                .where(
                    and_(
                        LawChunk.id != chunk_id,
                        LawChunk.embedding_vector.isnot(None),
                        LawChunk.embedding_vector != '',
                        LawChunk.is_processed == True
                    )
                )
            )
            
            result = await self.db.execute(chunks_query)
            rows = result.all()
            
            # Calculate similarities
            results = []
            for chunk, document in rows:
                try:
                    chunk_embedding = json.loads(chunk.embedding_vector)
                    similarity = self.embedding_service.cosine_similarity(
                        source_embedding,
                        chunk_embedding
                    )
                    
                    if similarity >= threshold:
                        results.append({
                            'chunk_id': chunk.id,
                            'content': chunk.content,
                            'similarity': float(similarity),
                            'chunk_index': chunk.chunk_index,
                            'document': {
                                'id': document.id,
                                'name': document.name,
                                'type': document.type,
                                'jurisdiction': document.jurisdiction
                            }
                        })
                        
                except Exception as e:
                    logger.warning(f"⚠️  Error processing chunk {chunk.id}: {str(e)}")
                    continue
            
            # Sort and limit
            results.sort(key=lambda x: x['similarity'], reverse=True)
            results = results[:top_k]
            
            logger.info(f"✅ Found {len(results)} similar chunks for chunk {chunk_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error finding similar chunks: {str(e)}")
            return []
    
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword matching.
        
        Args:
            query: Search query
            top_k: Number of results
            semantic_weight: Weight for semantic score (0.0 to 1.0)
            filters: Optional filters
            
        Returns:
            List of search results with hybrid scores
        """
        keyword_weight = 1.0 - semantic_weight
        
        # Get semantic results
        semantic_results = await self.search_similar_laws(
            query=query,
            top_k=top_k * 2,  # Get more for hybrid scoring
            threshold=0.5,  # Lower threshold for hybrid
            filters=filters
        )
        
        # Build query for keyword search
        query_builder = (
            select(LawChunk, LawDocument)
            .join(LawDocument, LawChunk.document_id == LawDocument.id)
            .where(
                or_(
                    LawChunk.content.ilike(f"%{query}%"),
                    LawDocument.name.ilike(f"%{query}%")
                )
            )
        )
        
        # Apply filters
        if filters:
            if 'document_id' in filters:
                query_builder = query_builder.where(
                    LawChunk.document_id == filters['document_id']
                )
            if 'jurisdiction' in filters:
                query_builder = query_builder.where(
                    LawDocument.jurisdiction.ilike(f"%{filters['jurisdiction']}%")
                )
        
        result = await self.db.execute(query_builder)
        keyword_results = result.all()
        
        # Combine results with hybrid scoring
        results_map = {}
        
        # Add semantic results
        for idx, res in enumerate(semantic_results):
            chunk_id = res['chunk_id']
            semantic_score = res['similarity']
            keyword_score = 0.0
            
            results_map[chunk_id] = {
                **res,
                'semantic_score': semantic_score,
                'keyword_score': keyword_score,
                'hybrid_score': semantic_weight * semantic_score + keyword_weight * keyword_score
            }
        
        # Add/update with keyword results
        for chunk, document in keyword_results[:top_k * 2]:
            chunk_id = chunk.id
            
            # Calculate keyword score (simple match count)
            query_lower = query.lower()
            content_lower = chunk.content.lower()
            keyword_score = min(1.0, content_lower.count(query_lower) * 0.1)
            
            if chunk_id in results_map:
                # Update existing
                results_map[chunk_id]['keyword_score'] = keyword_score
                results_map[chunk_id]['hybrid_score'] = (
                    semantic_weight * results_map[chunk_id]['semantic_score'] +
                    keyword_weight * keyword_score
                )
            else:
                # Add new
                results_map[chunk_id] = {
                    'chunk_id': chunk_id,
                    'content': chunk.content,
                    'chunk_index': chunk.chunk_index,
                    'word_count': chunk.word_count,
                    'semantic_score': 0.0,
                    'keyword_score': keyword_score,
                    'hybrid_score': keyword_weight * keyword_score,
                    'document': {
                        'id': document.id,
                        'name': document.name,
                        'type': document.type,
                        'jurisdiction': document.jurisdiction
                    }
                }
        
        # Sort by hybrid score and return top_k
        results = sorted(
            results_map.values(),
            key=lambda x: x['hybrid_score'],
            reverse=True
        )[:top_k]
        
        logger.info(f"✅ Hybrid search returned {len(results)} results")
        
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
            List of search suggestions
        """
        try:
            suggestions = []
            
            # Search in document names
            doc_query = (
                select(LawDocument.name)
                .where(LawDocument.name.ilike(f"%{partial_query}%"))
                .distinct()
                .limit(limit)
            )
            
            doc_result = await self.db.execute(doc_query)
            doc_names = doc_result.scalars().all()
            suggestions.extend(doc_names)
            
            # Remove duplicates and limit
            suggestions = list(set(suggestions))[:limit]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Error getting suggestions: {str(e)}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get search service statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            # Total chunks with embeddings
            total_chunks = await self.db.execute(
                select(func.count(LawChunk.id)).where(
                    and_(
                        LawChunk.embedding_vector.isnot(None),
                        LawChunk.embedding_vector != '',
                        LawChunk.is_processed == True
                    )
                )
            )
            total = total_chunks.scalar() or 0
            
            # Total documents
            total_docs = await self.db.execute(
                select(func.count(LawDocument.id))
            )
            docs_count = total_docs.scalar() or 0
            
            # Documents by status
            status_counts = await self.db.execute(
                select(
                    LawDocument.status,
                    func.count(LawDocument.id)
                ).group_by(LawDocument.status)
            )
            status_breakdown = {status: count for status, count in status_counts}
            
            return {
                'total_searchable_chunks': total,
                'total_documents': docs_count,
                'documents_by_status': status_breakdown,
                'cache_size': len(self._query_cache),
                'model': self.embedding_service.model_name
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {str(e)}")
            return {'error': str(e)}
    
    def clear_cache(self):
        """Clear the query cache."""
        self._query_cache.clear()
        logger.info("🗑️  Query cache cleared")
