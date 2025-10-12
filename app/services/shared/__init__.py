"""
Shared/Simplified services for law document processing.

These services work with the simplified LawDocument and LawChunk models.
"""
from .embedding_service import EmbeddingService
from .rag_service import RAGService
from .semantic_search_service import SemanticSearchService

__all__ = [
    'EmbeddingService',
    'RAGService',
    'SemanticSearchService',
]
