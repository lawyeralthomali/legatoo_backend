"""
RAG Service - Retrieval-Augmented Generation for Legal Laws

This service provides comprehensive RAG functionality specifically for legal laws:
- Law ingestion from JSON with hierarchical structure
- Intelligent text chunking with proper context preservation
- Semantic embeddings generation using Arabic-optimized models
- Similarity-based semantic search for law retrieval

Features:
- Arabic legal text normalization
- Context-aware chunking (preserves article metadata)
- Efficient batch processing
- Proper hierarchical linkage (LawSource → Article → Chunks)
- Production-ready error handling and logging
"""

import logging
import json
import re
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ..models.legal_knowledge import (
    LawSource, LawArticle, KnowledgeDocument, KnowledgeChunk
)
from ..services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG Service for Legal Laws - Production-ready implementation.
    
    Handles complete RAG pipeline:
    1. Law data ingestion from JSON
    2. Text chunking with context preservation
    3. Embedding generation for semantic search
    4. Similarity-based retrieval
    """
    def _build_chunk_text(self, law_name: Optional[str], article_number: Optional[str], article_title: Optional[str], body: str) -> str:
        header_parts = []
        if law_name:
            header_parts.append(law_name.strip())
        meta = []
        if article_number:
            meta.append(f"المادة {article_number}".strip())
        if article_title and article_title.strip():
            meta.append(article_title.strip())
        if meta:
            header_parts.append(" - ".join(meta))
        header = " | ".join(header_parts) if header_parts else ""
        return f"{header}\n{body or ''}".strip() if header else (body or '').strip()

    def __init__(self, db: AsyncSession):
        """
        Initialize RAG Service.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.embedding_service = EmbeddingService(db, model_name='default')
        
        # Chunking parameters
        self.max_chunk_tokens = 400  # Reduced for better granularity
        self.chunk_overlap_tokens = 50
        self.min_chunk_size = 10  # Much lower minimum for short articles
        
    # ==================== LAW INGESTION ====================
    
    async def ingest_law_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Ingest law data from JSON and create embeddings.
            
            This method:
            1. Validates JSON structure
            2. Creates/updates LawSource
            3. Creates LawArticles
            4. Chunks article content intelligently
            5. Generates embeddings for each chunk
            6. Stores chunks with proper hierarchical linkage
            
            Args:
                json_data: Dictionary containing law information and articles
                
            Returns:
                Dict with ingestion results and statistics
                
            Example JSON structure:
            {
                "law_name": "نظام العمل السعودي",
                "law_type": "law",
                "jurisdiction": "المملكة العربية السعودية",
                "issuing_authority": "وزارة الموارد البشرية والتنمية الاجتماعية",
                "issue_date": "2005-09-27",
                "articles": [
                    {
                        "article_number": "1",
                        "title": "التعريفات",
                        "content": "يقصد بالألفاظ والعبارات الآتية...",
                        "keywords": ["تعريفات", "مصطلحات"]
                    }
                ]
            }
            """
            start_time = datetime.utcnow()

            try:
                logger.info(f"📥 Starting law ingestion for: {json_data.get('law_name', 'Unknown')}")

                # Step 1: Validate JSON structure
                validation_result = self._validate_law_json(json_data)
                if not validation_result['valid']:
                    raise ValueError(f"Invalid JSON structure: {validation_result['errors']}")

                # Step 2: Parse dates
                issue_date = self._parse_date(json_data.get('issue_date'))
                last_update = self._parse_date(json_data.get('last_update'))

                # Step 3: Create KnowledgeDocument for metadata
                knowledge_doc = KnowledgeDocument(
                    title=json_data['law_name'],
                    category='law',
                    source_type='api_import',
                    status='raw',
                    document_metadata={
                        'jurisdiction': json_data.get('jurisdiction'),
                        'issuing_authority': json_data.get('issuing_authority'),
                        'issue_date': str(issue_date) if issue_date else None,
                        'source_url': json_data.get('source_url'),
                    }
                )
                self.db.add(knowledge_doc)
                await self.db.flush()

                logger.info(f"✅ Created KnowledgeDocument: {knowledge_doc.id}")

                # Step 4: Create LawSource
                law_source = LawSource(
                    name=json_data['law_name'],
                    type=json_data['law_type'],
                    jurisdiction=json_data.get('jurisdiction'),
                    issuing_authority=json_data.get('issuing_authority'),
                    issue_date=issue_date,
                    last_update=last_update,
                    description=json_data.get('description'),
                    source_url=json_data.get('source_url'),
                    knowledge_document_id=knowledge_doc.id,
                    status='raw'
                )
                self.db.add(law_source)
                await self.db.flush()

                logger.info(f"✅ Created LawSource: {law_source.id} - {law_source.name}")

                # Step 5: Process articles
                articles = json_data.get('articles', [])
                if not articles:
                    raise ValueError("No articles provided in JSON data")

                articles_created = 0
                chunks_created = 0

                for idx, article_data in enumerate(articles):
                    try:
                        # Create LawArticle
                        article = LawArticle(
                            law_source_id=law_source.id,
                            article_number=article_data.get('article_number', str(idx + 1)),
                            title=article_data.get('title'),
                            content=article_data['content'],
                            keywords=article_data.get('keywords', []),
                            order_index=idx,
                            source_document_id=knowledge_doc.id
                        )
                        self.db.add(article)
                        await self.db.flush()

                        articles_created += 1
                        logger.info(f"   📄 Article {article.article_number}: {article.title or 'No title'}")

                        # Step 6: Chunk article content
                        chunks = self.split_text_to_chunks(
                            text=article.content,
                            max_tokens=self.max_chunk_tokens
                        )

                        # Step 7: Create and embed chunks (WITH CONTEXT HEADER)
                        for chunk_idx, chunk_text in enumerate(chunks):
                            rich_chunk = self._build_chunk_text(
                                law_name=law_source.name,
                                article_number=article.article_number,
                                article_title=article.title,
                                body=chunk_text
                            )

                            embedding = await self.generate_embedding(rich_chunk)

                            chunk = KnowledgeChunk(
                                document_id=knowledge_doc.id,
                                chunk_index=chunk_idx,
                                content=rich_chunk,
                                tokens_count=len(rich_chunk.split()),
                                embedding_vector=json.dumps(embedding),
                                law_source_id=law_source.id,
                                article_id=article.id,
                                verified_by_admin=False
                            )
                            self.db.add(chunk)
                            chunks_created += 1

                        logger.info(f"      ✅ Created {len(chunks)} chunks for article {article.article_number}")

                    except Exception as e:
                        logger.error(f"❌ Failed to process article {idx + 1}: {str(e)}")
                        continue

                # Step 8: Update statuses
                law_source.status = 'processed'
                knowledge_doc.status = 'processed'
                knowledge_doc.processed_at = datetime.utcnow()

                # Commit all changes
                await self.db.commit()

                processing_time = (datetime.utcnow() - start_time).total_seconds()

                result = {
                    'success': True,
                    'law_source_id': law_source.id,
                    'law_name': law_source.name,
                    'knowledge_document_id': knowledge_doc.id,
                    'articles_created': articles_created,
                    'chunks_created': chunks_created,
                    'processing_time': round(processing_time, 2),
                    'status': 'processed'
                }

                logger.info(f"✅ Law ingestion completed: {articles_created} articles, {chunks_created} chunks in {processing_time:.2f}s")

                return result

            except Exception as e:
                logger.error(f"❌ Law ingestion failed: {str(e)}")
                await self.db.rollback()
                raise
        # ==================== EMBEDDING GENERATION ====================
        
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Uses the EmbeddingService with multilingual Arabic-optimized models.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            # Normalize Arabic text before embedding
            normalized_text = self.normalize_arabic_text(text)
            
            # Generate embedding using embedding service
            embedding = self.embedding_service._encode_text(normalized_text)
            
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {str(e)}")
            raise
    
    # ==================== SEMANTIC SEARCH ====================
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.6,
        law_source_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for relevant law chunks using semantic similarity.
        
        This method:
        1. Generates embedding for query
        2. Retrieves all law chunks with embeddings
        3. Computes cosine similarity
        4. Filters by threshold
        5. Returns top-k results with metadata
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            threshold: Minimum similarity threshold (0.0 to 1.0)
            law_source_id: Optional filter by specific law source
            
        Returns:
            Dict containing search results with law metadata
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"🔍 RAG Search: '{query[:50]}...' (top_k={top_k}, threshold={threshold})")
            
            # Step 1: Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Step 2: Build query for chunks with embeddings
            query_builder = (
                select(KnowledgeChunk)
                .where(
                    and_(
                        KnowledgeChunk.embedding_vector.isnot(None),
                        KnowledgeChunk.embedding_vector != '',
                        KnowledgeChunk.law_source_id.isnot(None)  # Only law chunks
                    )
                )
                .options(
                    selectinload(KnowledgeChunk.law_source),
                    selectinload(KnowledgeChunk.article)
                )
            )
            
            # Apply law source filter if provided
            if law_source_id:
                query_builder = query_builder.where(
                    KnowledgeChunk.law_source_id == law_source_id
                )
            
            result = await self.db.execute(query_builder)
            chunks = result.scalars().all()
            
            logger.info(f"📊 Found {len(chunks)} law chunks with embeddings")
            
            if not chunks:
                return {
                    'success': True,
                    'query': query,
                    'total_results': 0,
                    'results': [],
                    'processing_time': 0.0
                }
            
 
            # Step 3: Vectorized similarity + lexical blend + MMR
            emb_list, refs = [], []
            for ch in chunks:
                try:
                    emb_list.append(np.array(json.loads(ch.embedding_vector), dtype=np.float32))
                    refs.append(ch)
                except Exception:
                    continue

            if not emb_list:
                return {
                    'success': True,
                    'query': query,
                    'total_results': 0,
                    'results': [],
                    'processing_time': round((datetime.utcnow() - start_time).total_seconds(), 2)
                }

            E = np.vstack(emb_list).astype(np.float32)
            # L2 normalization for cosine
            E = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-12)
            q = np.array(query_embedding, dtype=np.float32)
            q = q / (np.linalg.norm(q) + 1e-12)

            # Pure cosine
            cos = E @ q  # (N,)

            # Lightweight lexical overlap (Arabic-safe)
            def _tokenize_ar(txt: str) -> List[str]:
                t = self.normalize_arabic_text(txt)
                t = re.sub(r'[^0-9\u0600-\u06FF\s]', ' ', t)
                return [x for x in t.split() if len(x) >= 2]

            q_tokens = _tokenize_ar(query)
            lex = np.zeros_like(cos)
            if len(q_tokens) > 0:
                qset = set(q_tokens)
                for i, ch in enumerate(refs):
                    cset = set(_tokenize_ar(ch.content))
                    inter = len(qset & cset); uni = len(qset | cset) or 1
                    lex[i] = inter / uni

            # Blended score
            alpha = 0.85  # semantic weight
            blended = alpha * cos + (1 - alpha) * lex

            # MMR selection for diversity
            def _mmr(qvec: np.ndarray, cand: np.ndarray, k: int, lam: float = 0.7) -> List[int]:
                if cand.shape[0] == 0:
                    return []
                qn = qvec / (np.linalg.norm(qvec) + 1e-12)
                cn = cand / (np.linalg.norm(cand, axis=1, keepdims=True) + 1e-12)
                sim_q = cn @ qn
                selected = []
                mask = np.ones(cn.shape[0], dtype=bool)
                while len(selected) < min(k, cn.shape[0]):
                    if not selected:
                        i = int(np.argmax(sim_q))
                        selected.append(i); mask[i] = False
                        continue
                    sel_mat = cn[selected]                    # (|S|, D)
                    red = sel_mat @ cn.T                      # (|S|, N)
                    max_red = red.max(axis=0)                 # (N,)
                    mmr = lam * sim_q - (1 - lam) * max_red
                    mmr[~mask] = -1e9
                    i = int(np.argmax(mmr))
                    selected.append(i); mask[i] = False
                return selected

            # Thresholding + MMR
            idxs = np.where(blended >= threshold)[0]
            if idxs.size == 0:
                topN = min(50, blended.shape[0])
                prelim = np.argpartition(-blended, topN)[:topN]
                mmr_sel = _mmr(q, E[prelim], k=top_k, lam=0.7)
                final = prelim[mmr_sel]
            else:
                cand = idxs
                mmr_sel = _mmr(q, E[cand], k=top_k, lam=0.7)
                final = cand[mmr_sel]

            ordered = sorted(list(final), key=lambda i: float(blended[i]), reverse=True)[:top_k]

            formatted_results = []
            for i in ordered:
                ch = refs[i]
                formatted_results.append({
                    'chunk_id': ch.id,
                    'content': ch.content,
                    'similarity_score': round(float(blended[i]), 4),
                    'law_source_id': ch.law_source.id if ch.law_source else None,
                    'law_source_name': ch.law_source.name if ch.law_source else None,
                    'article_id': ch.article.id if ch.article else None,
                    'article_number': ch.article.article_number if ch.article else None,
                    'article_title': ch.article.title if ch.article else None,
                })

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return {
                'success': True,
                'query': query,
                'total_results': len(formatted_results),
                'results': formatted_results,
                'processing_time': round(processing_time, 2)
            }
          
            
            # Step 4: Sort by similarity and take top-k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = similarities[:top_k]
            
            # Step 5: Format results
            formatted_results = []
            for item in top_results:
                chunk = item['chunk']
                similarity = item['similarity']
                
                formatted_results.append({
                    'chunk_id': chunk.id,
                    'content': chunk.content,
                    'similarity_score': round(similarity, 4),
                    'law_source_id': chunk.law_source.id if chunk.law_source else None,
                    'law_source_name': chunk.law_source.name if chunk.law_source else None,
                    'article_id': chunk.article.id if chunk.article else None,
                    'article_number': chunk.article.article_number if chunk.article else None,
                    'article_title': chunk.article.title if chunk.article else None,
                })
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Found {len(formatted_results)} results above threshold {threshold}")
            
            return {
                'success': True,
                'query': query,
                'total_results': len(formatted_results),
                'results': formatted_results,
                'processing_time': round(processing_time, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            raise
    
    # ==================== HELPER METHODS ====================
    
    def split_text_to_chunks(self, text: str, max_tokens: int = 400) -> List[str]:
        """
        Paragraph-first, then sentence split, with real token overlap between chunks.
        """
        text = self.normalize_arabic_text(text)
        if not text:
            return []

        # Split by paragraphs (double newline)
        paragraphs = re.split(r'\n\s*\n', text)
        base_chunks: List[str] = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            toks = paragraph.split()
            if self.min_chunk_size <= len(toks) <= max_tokens:
                base_chunks.append(paragraph)
                continue

            # Sentence split (Arabic-friendly)
            sentence_pattern = r'[.؟!]\s+|[،؛]\s+|\n+'
            sentences = [s.strip() for s in re.split(sentence_pattern, paragraph) if s.strip()]

            cur, cnt = [], 0
            for s in sentences:
                st = len(s.split())
                if st > max_tokens:
                    # hard split very long sentence by words window
                    words = s.split()
                    for i in range(0, len(words), max_tokens):
                        win = " ".join(words[i:i+max_tokens])
                        if len(win.split()) >= self.min_chunk_size:
                            if cur:
                                base_chunks.append(" ".join(cur))
                                cur, cnt = [], 0
                            base_chunks.append(win)
                    continue

                if cnt + st > max_tokens:
                    if cur:
                        ch = " ".join(cur)
                        if len(ch.split()) >= self.min_chunk_size:
                            base_chunks.append(ch)
                    cur, cnt = [s], st
                else:
                    cur.append(s)
                    cnt += st

            if cur:
                ch = " ".join(cur)
                if len(ch.split()) >= self.min_chunk_size:
                    base_chunks.append(ch)

        # Inject overlap between consecutive chunks
        if not base_chunks:
            return [text] if len(text.split()) >= self.min_chunk_size else []

        overlap = max(0, self.chunk_overlap_tokens)
        if overlap == 0:
            return base_chunks

        overlapped = []
        prev_tail_tokens: List[str] = []
        for idx, ch in enumerate(base_chunks):
            words = ch.split()
            if idx == 0:
                overlapped.append(ch)
            else:
                ch_ov = " ".join(prev_tail_tokens + words)
                overlapped.append(ch_ov)
            prev_tail_tokens = words[-overlap:] if len(words) > overlap else words[:]

        return overlapped


    def normalize_arabic_text(self, text: str) -> str:
        """
        Normalize Arabic text for better embedding quality.
        
        Applies:
        - Diacritics removal (tashkeel)
        - Alif normalization
        - Extra whitespace removal
        - Punctuation normalization
        
        Args:
            text: Input Arabic text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Remove Arabic diacritics (tashkeel)
        arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
        text = arabic_diacritics.sub('', text)
        
        # Normalize Alif variants
        text = re.sub(r'[إأآا]', 'ا', text)
        
        # Normalize Ya variants
        text = re.sub(r'ى', 'ي', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _calculate_cosine_similarity(
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
    
    def _validate_law_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate law JSON structure.
        
        Args:
            json_data: JSON data to validate
            
        Returns:
            Dict with validation results
        """
        errors = []
        
        # Required fields
        required_fields = ['law_name', 'law_type', 'articles']
        for field in required_fields:
            if field not in json_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate law_type
        valid_types = ['law', 'regulation', 'code', 'directive', 'decree']
        if 'law_type' in json_data and json_data['law_type'] not in valid_types:
            errors.append(f"Invalid law_type: {json_data['law_type']}. Must be one of: {valid_types}")
        
        # Validate articles
        if 'articles' in json_data:
            if not isinstance(json_data['articles'], list):
                errors.append("'articles' must be a list")
            elif len(json_data['articles']) == 0:
                errors.append("'articles' list cannot be empty")
            else:
                # Validate each article
                for idx, article in enumerate(json_data['articles']):
                    if not isinstance(article, dict):
                        errors.append(f"Article {idx} must be a dictionary")
                        continue
                    
                    if 'content' not in article:
                        errors.append(f"Article {idx} missing required field: content")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """
        Parse date string to date object.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Date object or None
        """
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse date '{date_str}': {str(e)}")
            return None

