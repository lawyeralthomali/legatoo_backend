"""
Semantic Chunking Service - Advanced Text Chunking for Arabic Legal Documents

This service implements semantic-based chunking instead of simple word-based chunking.
Preserves legal context and improves retrieval accuracy.

Key Features:
- Semantic boundary detection
- Legal structure preservation (articles, sections)
- Arabic text awareness
- Optimal chunk sizes for embeddings
- Context overlap for continuity
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a semantic chunk of text."""
    content: str
    start_pos: int
    end_pos: int
    chunk_index: int
    tokens_count: int
    article_number: Optional[str] = None
    section_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SemanticChunkingService:
    """
    خدمة التقسيم الدلالي للنصوص القانونية العربية
    
    Features:
    - Semantic boundary detection
    - Legal structure awareness
    - Optimal chunk sizing
    - Context preservation
    - Arabic-specific tokenization
    """
    
    # Legal structure patterns (Arabic)
    ARTICLE_PATTERNS = [
        r'المادة\s+(\d+)',
        r'المادة\s+\((\d+)\)',
        r'مادة\s+(\d+)',
        r'م\s*\.?\s*(\d+)',
        r'Article\s+(\d+)',
    ]
    
    SECTION_PATTERNS = [
        r'(الباب\s+[^\n]+)',
        r'(الفصل\s+[^\n]+)',
        r'(القسم\s+[^\n]+)',
        r'(الفرع\s+[^\n]+)',
    ]
    
    # Sentence boundary markers (Arabic)
    SENTENCE_ENDS = ['.', '。', '؟', '!', ':', '؛']
    
    def __init__(
        self,
        target_chunk_size: int = 400,
        min_chunk_size: int = 200,
        max_chunk_size: int = 600,
        overlap_size: int = 50
    ):
        """
        Initialize semantic chunking service.
        
        Args:
            target_chunk_size: Target tokens per chunk
            min_chunk_size: Minimum tokens per chunk
            max_chunk_size: Maximum tokens per chunk
            overlap_size: Overlap tokens between chunks
        """
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        
        logger.info(f"🔧 Semantic Chunking Service initialized")
        logger.info(f"   Target chunk size: {target_chunk_size} tokens")
        logger.info(f"   Min: {min_chunk_size}, Max: {max_chunk_size}")
        logger.info(f"   Overlap: {overlap_size} tokens")
    
    def tokenize_arabic(self, text: str) -> List[str]:
        """
        Tokenize Arabic text (simple word-based).
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Split on whitespace
        tokens = text.strip().split()
        
        return tokens
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenize_arabic(text))
    
    def detect_article_number(self, text: str) -> Optional[str]:
        """
        Detect article number in text.
        
        Args:
            text: Text to search
            
        Returns:
            Article number or None
        """
        for pattern in self.ARTICLE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def detect_section_name(self, text: str) -> Optional[str]:
        """
        Detect section/chapter name in text.
        
        Args:
            text: Text to search
            
        Returns:
            Section name or None
        """
        for pattern in self.SECTION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences (Arabic-aware).
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Replace sentence endings with special marker
        for end_char in self.SENTENCE_ENDS:
            text = text.replace(end_char, f'{end_char}|||SENT|||')
        
        # Split on marker
        sentences = [s.strip() for s in text.split('|||SENT|||') if s.strip()]
        
        return sentences
    
    def is_legal_boundary(self, text: str) -> bool:
        """
        Check if text represents a legal boundary (article, section).
        
        Args:
            text: Text to check
            
        Returns:
            True if legal boundary
        """
        # Check for article markers
        for pattern in self.ARTICLE_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Check for section markers
        for pattern in self.SECTION_PATTERNS:
            if re.match(pattern, text):
                return True
        
        return False
    
    def chunk_by_semantic_boundaries(
        self,
        text: str,
        language: str = 'ar'
    ) -> List[Chunk]:
        """
        Chunk text by semantic boundaries (main method).
        
        Args:
            text: Full document text
            language: Document language
            
        Returns:
            List of semantic chunks
        """
        logger.info(f"📝 Starting semantic chunking")
        logger.info(f"   Text length: {len(text)} characters")
        
        # Split into paragraphs
        paragraphs = self._split_into_paragraphs(text)
        logger.info(f"   Found {len(paragraphs)} paragraphs")
        
        # Split paragraphs into sentences
        sentences = []
        for para in paragraphs:
            para_sentences = self.split_into_sentences(para)
            sentences.extend(para_sentences)
        
        logger.info(f"   Found {len(sentences)} sentences")
        
        # Build chunks from sentences
        chunks = []
        current_chunk_sentences = []
        current_token_count = 0
        chunk_index = 0
        current_article = None
        current_section = None
        char_position = 0
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = self.count_tokens(sentence)
            
            # Detect article/section
            article = self.detect_article_number(sentence)
            section = self.detect_section_name(sentence)
            
            if article:
                current_article = article
            if section:
                current_section = section
            
            # Check if we should start a new chunk
            should_start_new = False
            
            # Reason 1: Current chunk is at target size
            if current_token_count >= self.target_chunk_size:
                should_start_new = True
            
            # Reason 2: Would exceed max size
            elif current_token_count + sentence_tokens > self.max_chunk_size:
                should_start_new = True
            
            # Reason 3: Legal boundary detected (article/section change)
            elif (article or section) and current_token_count >= self.min_chunk_size:
                should_start_new = True
            
            # Create new chunk if needed
            if should_start_new and current_chunk_sentences:
                chunk_content = ' '.join(current_chunk_sentences)
                
                chunks.append(Chunk(
                    content=chunk_content,
                    start_pos=char_position,
                    end_pos=char_position + len(chunk_content),
                    chunk_index=chunk_index,
                    tokens_count=current_token_count,
                    article_number=current_article,
                    section_name=current_section
                ))
                
                chunk_index += 1
                
                # Keep last N tokens for overlap
                if self.overlap_size > 0 and current_chunk_sentences:
                    overlap_sentences = self._get_overlap_sentences(
                        current_chunk_sentences,
                        self.overlap_size
                    )
                    current_chunk_sentences = overlap_sentences
                    current_token_count = sum(
                        self.count_tokens(s) for s in overlap_sentences
                    )
                else:
                    current_chunk_sentences = []
                    current_token_count = 0
                
                char_position += len(chunk_content)
            
            # Add sentence to current chunk
            current_chunk_sentences.append(sentence)
            current_token_count += sentence_tokens
        
        # Add final chunk
        if current_chunk_sentences:
            chunk_content = ' '.join(current_chunk_sentences)
            chunks.append(Chunk(
                content=chunk_content,
                start_pos=char_position,
                end_pos=char_position + len(chunk_content),
                chunk_index=chunk_index,
                tokens_count=current_token_count,
                article_number=current_article,
                section_name=current_section
            ))
        
        logger.info(f"✅ Created {len(chunks)} semantic chunks")
        self._log_chunk_statistics(chunks)
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newline or more
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _get_overlap_sentences(
        self,
        sentences: List[str],
        target_tokens: int
    ) -> List[str]:
        """
        Get last N sentences that approximate target token count.
        
        Args:
            sentences: List of sentences
            target_tokens: Target token count
            
        Returns:
            List of overlap sentences
        """
        overlap = []
        token_count = 0
        
        # Work backwards from end
        for sentence in reversed(sentences):
            sentence_tokens = self.count_tokens(sentence)
            if token_count + sentence_tokens > target_tokens:
                break
            overlap.insert(0, sentence)
            token_count += sentence_tokens
        
        return overlap
    
    def _log_chunk_statistics(self, chunks: List[Chunk]) -> None:
        """Log chunk statistics."""
        if not chunks:
            return
        
        token_counts = [c.tokens_count for c in chunks]
        avg_tokens = sum(token_counts) / len(token_counts)
        min_tokens = min(token_counts)
        max_tokens = max(token_counts)
        
        logger.info(f"📊 Chunk Statistics:")
        logger.info(f"   Average tokens: {avg_tokens:.1f}")
        logger.info(f"   Min tokens: {min_tokens}")
        logger.info(f"   Max tokens: {max_tokens}")
        logger.info(f"   Chunks with articles: {sum(1 for c in chunks if c.article_number)}")
    
    def chunks_to_dict(self, chunks: List[Chunk]) -> List[Dict[str, Any]]:
        """
        Convert chunks to dictionary format.
        
        Args:
            chunks: List of Chunk objects
            
        Returns:
            List of chunk dictionaries
        """
        return [
            {
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "tokens_count": chunk.tokens_count,
                "start_pos": chunk.start_pos,
                "end_pos": chunk.end_pos,
                "article_number": chunk.article_number,
                "section_name": chunk.section_name,
                "metadata": chunk.metadata or {}
            }
            for chunk in chunks
        ]
    
    def validate_chunks(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """
        Validate chunks meet quality criteria.
        
        Args:
            chunks: List of chunks
            
        Returns:
            Validation report
        """
        issues = []
        warnings = []
        
        for chunk in chunks:
            # Check minimum size
            if chunk.tokens_count < self.min_chunk_size:
                issues.append(f"Chunk {chunk.chunk_index} below minimum size: {chunk.tokens_count} tokens")
            
            # Check maximum size
            if chunk.tokens_count > self.max_chunk_size:
                issues.append(f"Chunk {chunk.chunk_index} exceeds maximum size: {chunk.tokens_count} tokens")
            
            # Check if empty
            if not chunk.content.strip():
                issues.append(f"Chunk {chunk.chunk_index} is empty")
            
            # Warning for very small chunks
            if chunk.tokens_count < 100:
                warnings.append(f"Chunk {chunk.chunk_index} is very small: {chunk.tokens_count} tokens")
        
        return {
            "valid": len(issues) == 0,
            "total_chunks": len(chunks),
            "issues": issues,
            "warnings": warnings
        }


class AdvancedSemanticChunker:
    """
    متقدم - خدمة التقسيم الدلالي المتقدمة
    
    Uses ML model to detect semantic boundaries (optional enhancement).
    """
    
    def __init__(self, base_chunker: SemanticChunkingService):
        """
        Initialize advanced chunker.
        
        Args:
            base_chunker: Base semantic chunker
        """
        self.base_chunker = base_chunker
        logger.info("🚀 Advanced Semantic Chunker initialized")
    
    def chunk_with_ml_boundaries(
        self,
        text: str,
        language: str = 'ar'
    ) -> List[Chunk]:
        """
        Chunk using ML-detected semantic boundaries.
        
        TODO: Implement ML-based boundary detection
        Currently falls back to base chunker.
        
        Args:
            text: Input text
            language: Document language
            
        Returns:
            List of chunks
        """
        logger.info("📝 Using ML-enhanced semantic chunking")
        
        # For now, use base chunker
        # Future: Add ML model for boundary detection
        return self.base_chunker.chunk_by_semantic_boundaries(text, language)
    
    def optimize_chunk_sizes(
        self,
        chunks: List[Chunk],
        target_size: int = 400
    ) -> List[Chunk]:
        """
        Optimize chunk sizes by merging or splitting.
        
        Args:
            chunks: Input chunks
            target_size: Target tokens per chunk
            
        Returns:
            Optimized chunks
        """
        logger.info(f"🔧 Optimizing chunk sizes (target: {target_size})")
        
        optimized = []
        buffer = []
        buffer_tokens = 0
        
        for chunk in chunks:
            # If buffer + chunk is close to target, merge
            if buffer and buffer_tokens + chunk.tokens_count <= target_size * 1.5:
                buffer.append(chunk)
                buffer_tokens += chunk.tokens_count
            else:
                # Flush buffer
                if buffer:
                    optimized.append(self._merge_chunks(buffer))
                buffer = [chunk]
                buffer_tokens = chunk.tokens_count
        
        # Flush final buffer
        if buffer:
            optimized.append(self._merge_chunks(buffer))
        
        logger.info(f"✅ Optimized from {len(chunks)} to {len(optimized)} chunks")
        
        return optimized
    
    def _merge_chunks(self, chunks: List[Chunk]) -> Chunk:
        """Merge multiple chunks into one."""
        if len(chunks) == 1:
            return chunks[0]
        
        merged_content = ' '.join(c.content for c in chunks)
        merged_tokens = sum(c.tokens_count for c in chunks)
        
        return Chunk(
            content=merged_content,
            start_pos=chunks[0].start_pos,
            end_pos=chunks[-1].end_pos,
            chunk_index=chunks[0].chunk_index,
            tokens_count=merged_tokens,
            article_number=chunks[0].article_number,
            section_name=chunks[0].section_name
        )

