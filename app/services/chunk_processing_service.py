"""
Chunk Processing Service for intelligent text splitting and processing.

This service handles the processing of knowledge chunks using AI-powered
text analysis to create semantically meaningful legal text segments.
"""

import os
import re
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import logging

from ..models.legal_knowledge import KnowledgeChunk
from ..repositories.legal_knowledge_repository import (
    KnowledgeDocumentRepository,
    KnowledgeChunkRepository
)

logger = logging.getLogger(__name__)


class GeminiTextProcessor:
    """
    Text processor using Google Gemini AI.
    
    This processor uses the official Google Gemini SDK to split legal text
    into semantically meaningful chunks. Supports both individual and batch processing.
    """
    
    # Batch processing configuration
    BATCH_SIZE = 12  # Process 12 chunks per API call
    MAX_BATCH_SIZE = 15
    MIN_BATCH_SIZE = 5
    
    def __init__(self):
        """Initialize Gemini text processor with API key."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self._client = None
    
    async def split_legal_text(self, text: str) -> List[str]:
        """
        Split legal text into sentences using Gemini AI.
        
        Args:
            text: The legal text to split
            
        Returns:
            List of sentences/chunks
        """
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found, using fallback")
            return self._fallback_split(text)
        
        # Initialize client if not already done
        if not self._client:
            try:
                from google import genai  # type: ignore
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Gemini SDK not available: {e}")
                return self._fallback_split(text)
        
        prompt = self._create_legal_splitting_prompt(text)
        
        try:
            # Call Gemini API with timeout protection
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=prompt
                ),
                timeout=60  # 1 minute timeout for text processing
            )
            
            text_response = getattr(resp, "text", "")
            if text_response:
                return self._parse_gemini_response(text_response)
            else:
                logger.warning("Empty response from Gemini, using fallback")
                return self._fallback_split(text)
                
        except asyncio.TimeoutError:
            logger.error("Gemini API timeout, using fallback")
            return self._fallback_split(text)
        except Exception as e:
            logger.error(f"Gemini request failed: {e}, using fallback")
            return self._fallback_split(text)
    
    def _create_legal_splitting_prompt(self, text: str) -> str:
        """
        Create prompt for legal text splitting.
        
        Args:
            text: The text to split
            
        Returns:
            Formatted prompt for Gemini AI
        """
        return f"""أنت مساعد متخصص في النصوص القانونية العربية. مهمتك تقسيم النص القانوني التالي إلى جمل مستقلة ذات معنى قانوني.

        **النص:** "{text}"

        **التعليمات:**
        1. قسم النص إلى جمل قانونية كاملة ذات معنى مستقل
        2. احتفظ بالمعنى القانوني الكامل
        3. لا تلخص أو تحذف معلومات مهمة
        4. ركز على الأفعال القانونية (يجب، يجوز، يعاقب، يحظر، إلخ)
        5. كل جملة يجب أن تكون مفهومة بشكل مستقل

        **المخرجات المطلوبة:**
        - قائمة بالجمل المنفصلة
        - كل جملة في سطر مستقل
        - بدون ترقيم أو رموز
        - لا تضع شروحات أو تعليقات إضافية

        قم الآن بتقسيم النص:"""
    
    def _parse_gemini_response(self, response_text: str) -> List[str]:
        """
        Parse Gemini AI response and extract sentences.
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            List of cleaned sentences
        """
        if not response_text:
            return []
        
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        sentences = []
        
        for line in lines:
            # Remove bullets, numbers, and other formatting
            clean_line = re.sub(r'^[\-\•\*\d\.\s]+', '', line).strip()
            
            # Filter out headers, empty lines, and very short text
            if (clean_line and len(clean_line) >= 10 and 
                not clean_line.startswith('**') and 
                not clean_line.endswith(':') and
                not clean_line.startswith('التعليمات') and
                not clean_line.startswith('المخرجات')):
                sentences.append(clean_line)
        
        return sentences
    
    def _fallback_split(self, text: str) -> List[str]:
        """
        Fallback method for text splitting without AI.
        
        Uses simple punctuation-based splitting when Gemini is unavailable.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences split by punctuation
        """
        # Simple split based on punctuation marks
        sentences = re.split(r'[\.!?،؛]', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    async def batch_split_legal_texts(self, texts: List[str]) -> Dict[int, List[str]]:
        """
        Split multiple legal texts in a single API call (BATCH PROCESSING).
        
        This method significantly reduces API costs and improves performance by
        processing multiple chunks in one request.
        
        Args:
            texts: List of text chunks to process
            
        Returns:
            Dictionary mapping text index to list of sentences
            Example: {0: ["sentence1", "sentence2"], 1: ["sentence3", "sentence4"]}
        """
        if not texts:
            return {}
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found, using fallback for batch")
            return {i: self._fallback_split(text) for i, text in enumerate(texts)}
        
        # Initialize client if needed
        if not self._client:
            try:
                from google import genai  # type: ignore
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Gemini SDK not available: {e}")
                return {i: self._fallback_split(text) for i, text in enumerate(texts)}
        
        prompt = self._create_batch_splitting_prompt(texts)
        
        try:
            logger.info(f"Processing batch of {len(texts)} texts with Gemini AI")
            
            # Call Gemini API with timeout protection
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=prompt
                ),
                timeout=120  # 2 minutes timeout for batch processing
            )
            
            text_response = getattr(resp, "text", "")
            if text_response:
                result = self._parse_batch_response(text_response, len(texts))
                logger.info(f"Successfully processed batch: {len(result)} texts parsed")
                return result
            else:
                logger.warning("Empty response from Gemini, using fallback for batch")
                return {i: self._fallback_split(text) for i, text in enumerate(texts)}
                
        except asyncio.TimeoutError:
            logger.error("Gemini API timeout for batch, using fallback")
            return {i: self._fallback_split(text) for i, text in enumerate(texts)}
        except Exception as e:
            logger.error(f"Batch processing failed: {e}, using fallback")
            return {i: self._fallback_split(text) for i, text in enumerate(texts)}
    
    def _create_batch_splitting_prompt(self, texts: List[str]) -> str:
        """
        Create prompt for batch processing multiple texts.
        
        Args:
            texts: List of texts to process
            
        Returns:
            Formatted batch prompt
        """
        # Build the text sections
        text_sections = []
        for i, text in enumerate(texts, 1):
            text_sections.append(f"نص {i}:\n{text}")
        
        texts_combined = "\n\n".join(text_sections)
        
        return f"""أنت مساعد متخصص في معالجة النصوص القانونية العربية. مهمتك تقسيم كل نص من النصوص التالية إلى جمل قانونية مستقلة ذات معنى كامل.

**النصوص المطلوب معالجتها:**

{texts_combined}

**التعليمات:**
1. قسم كل نص إلى جمل قانونية كاملة ذات معنى مستقل
2. احتفظ بالمعنى القانوني الكامل لكل جملة
3. لا تلخص أو تحذف معلومات مهمة
4. ركز على الأفعال القانونية (يجب، يجوز، يعاقب، يحظر، إلخ)
5. كل جملة يجب أن تكون مفهومة بشكل مستقل

**تنسيق المخرجات:**
أرجع النتائج بنفس ترتيب النصوص مع فصل واضح بين كل نص:

=== نص 1 ===
- الجملة الأولى
- الجملة الثانية
...

=== نص 2 ===
- الجملة الأولى
- الجملة الثانية
...

**ملاحظات مهمة:**
- احافظ على ترتيب النصوص (1، 2، 3، ...)
- ضع كل جملة في سطر مستقل مع علامة (-)
- لا تضع شروحات أو تعليقات إضافية
- ابدأ مباشرة بالنتائج

قم الآن بتقسيم النصوص:"""
    
    def _parse_batch_response(self, response_text: str, expected_count: int) -> Dict[int, List[str]]:
        """
        Parse batch response from Gemini and map sentences to original texts.
        
        Args:
            response_text: Raw response from Gemini
            expected_count: Number of texts we sent
            
        Returns:
            Dictionary mapping text index to sentences
        """
        if not response_text:
            return {}
        
        result = {}
        current_text_idx = None
        
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for text separator (=== نص 1 ===, === نص 2 ===, etc.)
            if line.startswith('===') or line.startswith('نص'):
                # Extract text number
                import re
                match = re.search(r'نص\s*(\d+)', line)
                if match:
                    text_num = int(match.group(1))
                    current_text_idx = text_num - 1  # Convert to 0-based index
                    if current_text_idx not in result:
                        result[current_text_idx] = []
                continue
            
            # Parse sentence lines (starting with - or • or just text)
            clean_line = re.sub(r'^[\-\•\*\d\.\)\s]+', '', line).strip()
            
            # Filter valid sentences
            if (clean_line and 
                len(clean_line) >= 10 and 
                not clean_line.startswith('**') and 
                not clean_line.endswith(':') and
                not clean_line.startswith('التعليمات') and
                not clean_line.startswith('المخرجات') and
                not clean_line.startswith('===') and
                current_text_idx is not None):
                result[current_text_idx].append(clean_line)
        
        # Validate we got results for all texts
        if len(result) != expected_count:
            logger.warning(f"Batch parsing incomplete: expected {expected_count}, got {len(result)} texts")
        
        return result

class ChunkProcessingService:
    """
    Service for processing knowledge chunks.
    
    This service handles the intelligent processing of document chunks,
    splitting them into semantically meaningful legal segments using AI.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize chunk processing service with database session."""
        self.db = db
        self.document_repo = KnowledgeDocumentRepository(db)
        self.chunk_repo = KnowledgeChunkRepository(db)
        self.gemini_processor = GeminiTextProcessor()
    
    async def process_document_chunks(self, document_id: int) -> Dict[str, Any]:
        """
        Process all chunks in a document using BATCH processing for efficiency.
        
        This method uses batch processing to reduce API calls by 80-90%:
        - Groups chunks into batches of 10-15
        - Sends batches to Gemini AI in single requests
        - Falls back to individual processing on failure
        
        Args:
            document_id: ID of the document to process
            
        Returns:
            Dict containing success status, message, and processing results
        """
        try:
            # Verify document exists
            document = await self.document_repo.get_document_by_id(document_id)
            if not document:
                return {
                    "success": False,
                    "message": f"Document with ID {document_id} not found",
                    "data": None,
                    "errors": [{"field": "document_id", "message": "Document not found"}]
                }
            
            # Get original chunks
            original_chunks = await self.chunk_repo.get_chunks_by_document(document_id)
            if not original_chunks:
                return {
                    "success": False,
                    "message": f"No chunks found for document {document_id}",
                    "data": None,
                    "errors": [{"field": "document_id", "message": "No chunks found"}]
                }
            
            logger.info(f"Starting batch processing for document {document_id} with {len(original_chunks)} chunks")
            
            # Process chunks in batches
            processing_results = []
            total_new_chunks = 0
            total_api_calls = 0
            
            batch_size = self.gemini_processor.BATCH_SIZE
            
            for i in range(0, len(original_chunks), batch_size):
                batch = original_chunks[i:i + batch_size]
                batch_result = await self._process_batch_chunks(batch)
                
                processing_results.extend(batch_result['details'])
                total_new_chunks += batch_result['new_chunks_count']
                total_api_calls += batch_result['api_calls']
            
            # Update document status to processed
            await self.document_repo.update_document_status(
                document_id, 
                "processed",
                datetime.now()
            )
            
            # Calculate efficiency metrics
            original_api_calls = len(original_chunks)  # Without batching
            savings_percent = ((original_api_calls - total_api_calls) / original_api_calls * 100) if original_api_calls > 0 else 0
            
            logger.info(f"Batch processing complete: {total_api_calls} API calls vs {original_api_calls} without batching ({savings_percent:.1f}% reduction)")
            
            return {
                "success": True,
                "message": f"Processed {len(original_chunks)} chunks into {total_new_chunks} smart chunks using {total_api_calls} API calls",
                "data": {
                    "document_id": document_id,
                    "document_title": document.title,
                    "original_chunks_count": len(original_chunks),
                    "new_smart_chunks_count": total_new_chunks,
                    "processing_details": processing_results,
                    "performance_metrics": {
                        "api_calls_made": total_api_calls,
                        "api_calls_without_batching": original_api_calls,
                        "api_calls_saved": original_api_calls - total_api_calls,
                        "cost_reduction_percent": f"{savings_percent:.1f}%",
                        "batch_size_used": batch_size
                    }
                },
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"Chunk processing failed: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Processing failed: {str(e)}",
                "data": None,
                "errors": [{"field": None, "message": str(e)}]
            }
    
    async def _process_batch_chunks(self, chunks: List[KnowledgeChunk]) -> Dict[str, Any]:
        """
        Process a batch of chunks using Gemini AI batch processing.
        
        Args:
            chunks: List of chunks to process in batch
            
        Returns:
            Dict with processing results and metrics
        """
        if not chunks:
            return {
                "details": [],
                "new_chunks_count": 0,
                "api_calls": 0
            }
        
        # Extract texts from chunks
        texts = [chunk.content for chunk in chunks]
        
        try:
            # Try batch processing first
            logger.info(f"Processing batch of {len(chunks)} chunks")
            batch_results = await self.gemini_processor.batch_split_legal_texts(texts)
            
            # Check if batch processing succeeded
            if len(batch_results) == len(chunks):
                # Batch processing successful
                details = []
                total_new_chunks = 0
                
                for idx, chunk in enumerate(chunks):
                    sentences = batch_results.get(idx, [])
                    
                    # Create smart chunks from sentences
                    new_chunks = []
                    for sent_idx, sentence in enumerate(sentences):
                        if self._is_legally_meaningful(sentence):
                            smart_chunk = self._create_smart_chunk(chunk, sentence, sent_idx)
                            new_chunks.append(smart_chunk)
                    
                    # Save chunks if any
                    if new_chunks:
                        await self.chunk_repo.save_chunks_batch(new_chunks)
                    
                    details.append({
                        "original_chunk_id": chunk.id,
                        "original_content_preview": chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content,
                        "smart_sentences_count": len(sentences),
                        "new_chunks_count": len(new_chunks),
                        "processing_method": "gemini_batch"
                    })
                    
                    total_new_chunks += len(new_chunks)
                
                logger.info(f"Batch processing successful: {len(chunks)} chunks -> {total_new_chunks} smart chunks")
                
                return {
                    "details": details,
                    "new_chunks_count": total_new_chunks,
                    "api_calls": 1  # One API call for entire batch
                }
            else:
                # Batch parsing incomplete, fallback to individual
                logger.warning(f"Batch parsing incomplete, falling back to individual processing for {len(chunks)} chunks")
                return await self._process_chunks_individually(chunks)
                
        except Exception as e:
            # Batch processing failed, fallback to individual
            logger.error(f"Batch processing error: {e}, falling back to individual processing")
            return await self._process_chunks_individually(chunks)
    
    async def _process_chunks_individually(self, chunks: List[KnowledgeChunk]) -> Dict[str, Any]:
        """
        Fallback method: Process chunks individually when batch processing fails.
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            Dict with processing results
        """
        details = []
        total_new_chunks = 0
        
        for chunk in chunks:
            result = await self._process_single_chunk(chunk)
            details.append(result)
            total_new_chunks += result['new_chunks_count']
        
        return {
            "details": details,
            "new_chunks_count": total_new_chunks,
            "api_calls": len(chunks)  # One API call per chunk
        }
    
    async def _process_single_chunk(self, original_chunk: KnowledgeChunk) -> Dict[str, Any]:
        """
        Process a single chunk and split it into smart chunks.
        
        Args:
            original_chunk: The chunk to process
            
        Returns:
            Dict containing processing statistics
        """
        # Split text into smart sentences using Gemini AI
        smart_sentences = await self.gemini_processor.split_legal_text(original_chunk.content)
        
        # Create new smart chunks
        new_chunks = []
        for index, sentence in enumerate(smart_sentences):
            if self._is_legally_meaningful(sentence):
                smart_chunk = self._create_smart_chunk(original_chunk, sentence, index)
                new_chunks.append(smart_chunk)
        
        # Save new chunks in batch
        if new_chunks:
            await self.chunk_repo.save_chunks_batch(new_chunks)
        
        return {
            "original_chunk_id": original_chunk.id,
            "original_content_preview": original_chunk.content[:100] + "..." if len(original_chunk.content) > 100 else original_chunk.content,
            "smart_sentences_count": len(smart_sentences),
            "new_chunks_count": len(new_chunks),
            "processing_method": "gemini_ai"
        }
    
    def _is_legally_meaningful(self, sentence: str) -> bool:
        """
        Check if a sentence has legal meaning and value.
        
        Args:
            sentence: The sentence to check
            
        Returns:
            True if the sentence is legally meaningful, False otherwise
        """
        if not sentence or len(sentence.strip()) < 10:
            return False
        
        # Check for meaningless patterns
        meaningless_patterns = [r'^\d+$', r'^[\.\-\*]+$', r'.*(إلخ|إلخ\.|الخ\.|الخ)$']
        for pattern in meaningless_patterns:
            if re.match(pattern, sentence.strip()):
                return False
        
        # Legal indicators in Arabic
        legal_indicators = [
            'يجب', 'يلزم', 'يجوز', 'يعاقب', 'يحكم', 'يشترط',
            'مادة', 'قانون', 'نظام', 'عقوبة', 'تعويض', 'حق',
            'التزام', 'مسؤولية', 'عقد', 'اتفاق', 'محكمة'
        ]
        
        return any(indicator in sentence for indicator in legal_indicators)
    
    def _create_smart_chunk(
        self, 
        original_chunk: KnowledgeChunk, 
        content: str, 
        chunk_index: int
    ) -> KnowledgeChunk:
        """
        Create a new smart chunk from original chunk.
        
        Args:
            original_chunk: The original chunk to base the new chunk on
            content: The content for the new smart chunk
            chunk_index: The index of the new chunk
            
        Returns:
            A new KnowledgeChunk instance
        """
        return KnowledgeChunk(
            document_id=original_chunk.document_id,
            chunk_index=chunk_index,
            content=content,
            tokens_count=len(content.split()),
            embedding=None,
            verified_by_admin=False,
            law_source_id=getattr(original_chunk, 'law_source_id', None),
            branch_id=getattr(original_chunk, 'branch_id', None),
            chapter_id=getattr(original_chunk, 'chapter_id', None),
            article_id=getattr(original_chunk, 'article_id', None),
            case_id=getattr(original_chunk, 'case_id', None),
            term_id=getattr(original_chunk, 'term_id', None)
        )
    
    async def get_processing_status(self, document_id: int) -> Dict[str, Any]:
        """
        Get the processing status for a document's chunks.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Dict containing processing status and statistics
        """
        stats = await self.chunk_repo.get_chunks_statistics(document_id)
        document = await self.document_repo.get_document_by_id(document_id)
        
        progress = 0
        if stats["total_chunks"] > 0:
            progress = (stats["chunks_with_embeddings"] / stats["total_chunks"]) * 100
        
        return {
            "document_id": document_id,
            "document_title": document.title if document else "Unknown",
            "total_chunks": stats["total_chunks"],
            "chunks_with_embeddings": stats["chunks_with_embeddings"],
            "processing_progress": f"{progress:.1f}%",
            "status": document.status if document else "unknown"
        }