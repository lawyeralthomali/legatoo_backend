"""
FAISS Vector Search Service - Phase 4 Implementation

This service handles:
- FAISS index creation and management
- Vector similarity search (Top-N results)
- Index persistence (save/load)
- Hybrid search (vector + metadata filters)
- Real-time index updates

FAISS (Facebook AI Similarity Search):
- Efficient similarity search in high-dimensional spaces
- Supports billions of vectors
- Multiple index types (Flat, IVF, HNSW)
"""

import os
import logging
import pickle
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import numpy as np
import faiss
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.legal_document2 import LegalDocumentChunk, LegalDocument

logger = logging.getLogger(__name__)


class FAISSSearchService:
    """
    FAISS-based vector search service.
    
    Phase 4 Implementation:
    - Create and manage FAISS index
    - Add/update/remove vectors
    - Search for Top-N similar chunks
    - Persistent storage
    """

    def __init__(
        self,
        embedding_dimension: int = 768,
        index_path: str = "faiss_indexes",
        index_type: str = "Flat"
    ):
        """
        Initialize FAISS search service.
        
        Args:
            embedding_dimension: Dimension of embedding vectors
            index_path: Directory to store FAISS indexes
            index_type: FAISS index type ('Flat', 'IVF', 'HNSW')
        """
        self.embedding_dimension = embedding_dimension
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.index_type = index_type
        self.index = None
        self.chunk_id_map = {}  # Maps FAISS index position to chunk ID
        
        logger.info(f"FAISS service initialized: dim={embedding_dimension}, type={index_type}")

    # ==================== PHASE 4: INDEX CREATION ====================

    def create_index(self, force_recreate: bool = False):
        """
        Create a new FAISS index.
        
        Phase 4: Index initialization
        
        Args:
            force_recreate: If True, recreate even if exists
        """
        if self.index is not None and not force_recreate:
            logger.info("FAISS index already exists")
            return
        
        if self.index_type == "Flat":
            # L2 (Euclidean) distance - exact search
            self.index = faiss.IndexFlatL2(self.embedding_dimension)
            logger.info("Created FAISS Flat index (exact search)")
        
        elif self.index_type == "IVF":
            # Inverted File Index - faster approximate search
            quantizer = faiss.IndexFlatL2(self.embedding_dimension)
            nlist = 100  # Number of clusters
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dimension, nlist)
            self.index.nprobe = 10  # Number of clusters to search
            logger.info("Created FAISS IVF index (approximate search)")
        
        elif self.index_type == "HNSW":
            # Hierarchical Navigable Small World - very fast approximate search
            M = 32  # Number of connections per layer
            self.index = faiss.IndexHNSWFlat(self.embedding_dimension, M)
            logger.info("Created FAISS HNSW index (fast approximate search)")
        
        else:
            # Default to Flat
            self.index = faiss.IndexFlatL2(self.embedding_dimension)
            logger.info("Created FAISS Flat index (default)")
        
        # Reset chunk ID map
        self.chunk_id_map = {}

    async def build_index_from_database(self, db: AsyncSession):
        """
        Build FAISS index from all chunks in database.
        
        Phase 4: Initial index population from existing data
        
        Args:
            db: Database session
        """
        logger.info("Building FAISS index from database...")
        
        # Create new index
        self.create_index(force_recreate=True)
        
        # Get all chunks with embeddings
        result = await db.execute(
            select(LegalDocumentChunk)
            .filter(LegalDocumentChunk.embedding.isnot(None))
        )
        chunks = result.scalars().all()
        
        if not chunks:
            logger.warning("No chunks with embeddings found in database")
            return
        
        # Extract embeddings and build index
        embeddings = []
        chunk_ids = []
        
        for chunk in chunks:
            if chunk.embedding and len(chunk.embedding) > 0:
                embeddings.append(chunk.embedding)
                chunk_ids.append(chunk.id)
        
        if embeddings:
            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Train index if needed (for IVF)
            if self.index_type == "IVF" and not self.index.is_trained:
                logger.info("Training IVF index...")
                self.index.train(embeddings_array)
            
            # Add embeddings to index
            self.index.add(embeddings_array)
            
            # Update chunk ID mapping
            for i, chunk_id in enumerate(chunk_ids):
                self.chunk_id_map[i] = chunk_id
            
            logger.info(f"✅ Built FAISS index with {len(embeddings)} vectors")
        else:
            logger.warning("No valid embeddings found")

    # ==================== PHASE 4: ADD/UPDATE VECTORS ====================

    async def add_chunk_embedding(
        self,
        chunk_id: int,
        embedding: List[float]
    ):
        """
        Add a single chunk embedding to the index.
        
        Phase 4: Real-time index updates
        
        Args:
            chunk_id: Chunk ID
            embedding: Embedding vector
        """
        if self.index is None:
            self.create_index()
        
        # Convert to numpy array
        embedding_array = np.array([embedding], dtype=np.float32)
        
        # Add to index
        position = self.index.ntotal
        self.index.add(embedding_array)
        
        # Update mapping
        self.chunk_id_map[position] = chunk_id
        
        logger.debug(f"Added embedding for chunk {chunk_id} at position {position}")

    async def add_batch_embeddings(
        self,
        chunk_embeddings: List[Tuple[int, List[float]]]
    ):
        """
        Add multiple chunk embeddings to the index.
        
        Args:
            chunk_embeddings: List of (chunk_id, embedding) tuples
        """
        if self.index is None:
            self.create_index()
        
        if not chunk_embeddings:
            return
        
        # Separate chunk IDs and embeddings
        chunk_ids = [chunk_id for chunk_id, _ in chunk_embeddings]
        embeddings = [embedding for _, embedding in chunk_embeddings]
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Add to index
        start_position = self.index.ntotal
        self.index.add(embeddings_array)
        
        # Update mapping
        for i, chunk_id in enumerate(chunk_ids):
            self.chunk_id_map[start_position + i] = chunk_id
        
        logger.info(f"Added {len(chunk_embeddings)} embeddings to index")

    # ==================== PHASE 4: VECTOR SEARCH ====================

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        db: Optional[AsyncSession] = None,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        similarity_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Search for most similar chunks using FAISS.
        
        Phase 4: Vector similarity search with metadata filtering
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            db: Database session (optional, for metadata filtering)
            document_type: Filter by document type
            language: Filter by language
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of search results with chunk and similarity score
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("FAISS index is empty")
            return []
        
        # Convert to numpy array
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search in FAISS
        # Return more results if filtering is needed
        search_k = top_k * 10 if (document_type or language) else top_k
        distances, indices = self.index.search(query_array, search_k)
        
        # Convert distances to similarity scores (L2 to cosine-like)
        # Lower distance = higher similarity
        max_distance = np.max(distances[0]) if len(distances[0]) > 0 else 1.0
        similarities = 1.0 - (distances[0] / (max_distance + 1e-10))
        
        # Get chunk IDs from indices
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if idx == -1:  # FAISS returns -1 for padding
                continue
            
            chunk_id = self.chunk_id_map.get(int(idx))
            if chunk_id is None:
                continue
            
            # Apply similarity threshold
            if similarity < similarity_threshold:
                continue
            
            results.append({
                'chunk_id': chunk_id,
                'similarity_score': float(similarity),
                'faiss_index': int(idx)
            })
        
        # If database session provided, fetch chunk data and apply filters
        if db:
            results = await self._enrich_results_with_metadata(
                db, results, document_type, language
            )
        
        # Sort by similarity and limit to top_k
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        results = results[:top_k]
        
        logger.info(f"FAISS search found {len(results)} results")
        return results

    async def _enrich_results_with_metadata(
        self,
        db: AsyncSession,
        results: List[Dict],
        document_type: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[Dict]:
        """
        Enrich search results with chunk and document metadata.
        
        Apply metadata filters if specified.
        
        Args:
            db: Database session
            results: List of search results from FAISS
            document_type: Filter by document type
            language: Filter by language
            
        Returns:
            Enriched and filtered results
        """
        if not results:
            return []
        
        # Get chunk IDs
        chunk_ids = [r['chunk_id'] for r in results]
        
        # Query chunks with document metadata
        query = (
            select(LegalDocumentChunk, LegalDocument)
            .join(LegalDocument, LegalDocumentChunk.document_id == LegalDocument.id)
            .filter(LegalDocumentChunk.id.in_(chunk_ids))
        )
        
        # Apply filters
        if document_type:
            from ..models.legal_document2 import DocumentTypeEnum
            # Convert string to enum value
            try:
                doc_type_enum = DocumentTypeEnum(document_type)
                query = query.filter(LegalDocument.document_type == doc_type_enum)
            except ValueError:
                # If invalid document type, skip the filter
                pass
        
        if language:
            from ..models.legal_document2 import LanguageEnum
            # Convert string to enum value
            try:
                lang_enum = LanguageEnum(language)
                query = query.filter(LegalDocument.language == lang_enum)
            except ValueError:
                # If invalid language, skip the filter
                pass
        
        result = await db.execute(query)
        rows = result.all()
        
        # Create lookup dictionary
        chunk_data = {}
        for chunk, document in rows:
            chunk_data[chunk.id] = {
                'chunk': chunk,
                'document': document
            }
        
        # Enrich results
        enriched_results = []
        for r in results:
            chunk_id = r['chunk_id']
            if chunk_id in chunk_data:
                data = chunk_data[chunk_id]
                enriched_results.append({
                    'chunk': data['chunk'],
                    'document': data['document'],
                    'similarity_score': r['similarity_score'],
                    'highlights': []  # Can be populated later
                })
        
        return enriched_results

    # ==================== PHASE 4: INDEX PERSISTENCE ====================

    def save_index(self, filename: str = "faiss_index.bin"):
        """
        Save FAISS index to disk.
        
        Phase 4: Persistent storage
        
        Args:
            filename: Filename for the index
        """
        if self.index is None:
            logger.warning("No index to save")
            return
        
        index_file = self.index_path / filename
        mapping_file = self.index_path / f"{filename}.mapping"
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_file))
        
        # Save chunk ID mapping
        with open(mapping_file, 'wb') as f:
            pickle.dump(self.chunk_id_map, f)
        
        logger.info(f"✅ Saved FAISS index to {index_file}")
        logger.info(f"   Index size: {self.index.ntotal} vectors")

    def load_index(self, filename: str = "faiss_index.bin") -> bool:
        """
        Load FAISS index from disk.
        
        Phase 4: Load pre-built index
        
        Args:
            filename: Filename of the index
            
        Returns:
            True if loaded successfully, False otherwise
        """
        index_file = self.index_path / filename
        mapping_file = self.index_path / f"{filename}.mapping"
        
        if not index_file.exists():
            logger.warning(f"Index file not found: {index_file}")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_file))
            
            # Load chunk ID mapping
            if mapping_file.exists():
                with open(mapping_file, 'rb') as f:
                    self.chunk_id_map = pickle.load(f)
            else:
                logger.warning("Chunk ID mapping not found")
                self.chunk_id_map = {}
            
            logger.info(f"✅ Loaded FAISS index from {index_file}")
            logger.info(f"   Index size: {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}")
            return False

    def clear_index(self):
        """
        Clear the FAISS index and chunk ID mapping.
        """
        self.index = None
        self.chunk_id_map = {}
        logger.info("FAISS index cleared")

    # ==================== UTILITY METHODS ====================

    def get_index_stats(self) -> Dict:
        """
        Get statistics about the current FAISS index.
        
        Returns:
            Dictionary with index statistics
        """
        if self.index is None:
            return {
                'exists': False,
                'total_vectors': 0,
                'dimension': self.embedding_dimension,
                'index_type': self.index_type
            }
        
        return {
            'exists': True,
            'total_vectors': self.index.ntotal,
            'dimension': self.embedding_dimension,
            'index_type': self.index_type,
            'is_trained': getattr(self.index, 'is_trained', True),
            'chunk_mapping_size': len(self.chunk_id_map)
        }

    async def remove_chunk_embedding(self, chunk_id: int):
        """
        Remove a chunk embedding from the index.
        
        Note: FAISS doesn't support direct deletion.
        This marks the chunk for exclusion and requires rebuild for full removal.
        
        Args:
            chunk_id: Chunk ID to remove
        """
        # Find and remove from mapping
        positions_to_remove = [
            pos for pos, cid in self.chunk_id_map.items()
            if cid == chunk_id
        ]
        
        for pos in positions_to_remove:
            del self.chunk_id_map[pos]
        
        logger.info(f"Removed chunk {chunk_id} from mapping (rebuild needed for full removal)")

    async def rebuild_index(self, db: AsyncSession):
        """
        Rebuild the entire FAISS index from database.
        
        Use this after many deletions or updates.
        
        Args:
            db: Database session
        """
        logger.info("Rebuilding FAISS index from database...")
        await self.build_index_from_database(db)
        self.save_index()
        logger.info("✅ FAISS index rebuilt and saved")

