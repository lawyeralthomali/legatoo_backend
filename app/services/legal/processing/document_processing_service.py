"""
Document Processing Service for text extraction and chunking.

This service handles the extraction of text from various document formats,
intelligent chunking, and legal entity detection for Arabic and English documents.
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import asyncio

# Document processing libraries
import PyPDF2
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Service for processing legal documents."""

    # Arabic legal patterns
    ARABIC_ARTICLE_PATTERN = r'(?:المادة|الماده|مادة)\s*(?:رقم)?\s*(\d+|[٠-٩]+)'
    ARABIC_SECTION_PATTERN = r'(?:الباب|الفصل|القسم)\s*(?:ال)?(\w+)'
    
    # English legal patterns
    ENGLISH_ARTICLE_PATTERN = r'(?:Article|Section|Clause)\s+(?:No\.?\s*)?(\d+)'
    ENGLISH_SECTION_PATTERN = r'(?:Chapter|Part|Section)\s+(\w+)'

    def __init__(self):
        """Initialize document processing service."""
        pass

    async def extract_text_from_file(
        self,
        file_path: str,
        file_extension: str
    ) -> str:
        """
        Extract text from uploaded file.
        
        Args:
            file_path: Path to the uploaded file
            file_extension: File extension (.pdf, .docx, .txt)
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If file format is unsupported
        """
        try:
            if file_extension.lower() == '.pdf':
                return await self._extract_from_pdf(file_path)
            elif file_extension.lower() in ['.docx', '.doc']:
                return await self._extract_from_docx(file_path)
            elif file_extension.lower() == '.txt':
                return await self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise

    async def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file using PyPDF2.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_pdf_sync, file_path)

    def _extract_pdf_sync(self, file_path: str) -> str:
        """Synchronous PDF extraction."""
        text_content = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num}: {str(e)}")
                    continue
        
        return '\n\n'.join(text_content)

    async def _extract_from_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_docx_sync, file_path)

    def _extract_docx_sync(self, file_path: str) -> str:
        """Synchronous DOCX extraction."""
        document = DocxDocument(file_path)
        paragraphs = [para.text for para in document.paragraphs if para.text.strip()]
        return '\n\n'.join(paragraphs)

    async def _extract_from_txt(self, file_path: str) -> str:
        """
        Extract text from TXT file.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Extracted text
        """
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Fallback to other encodings for Arabic text
            for encoding in ['cp1256', 'iso-8859-6', 'utf-16']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("Could not decode text file with supported encodings")

    async def chunk_text(
        self,
        text: str,
        language: str,
        min_chunk_size: int = 200,
        max_chunk_size: int = 500,
        overlap: int = 50
    ) -> List[Dict[str, any]]:
        """
        Split text into context-aware chunks.
        
        This method intelligently chunks documents while:
        - Preserving sentence and paragraph boundaries
        - Maintaining legal context (articles, sections)
        - Handling Arabic and English text properly
        
        Args:
            text: Full document text
            language: Document language (ar, en, fr)
            min_chunk_size: Minimum chunk size in words
            max_chunk_size: Maximum chunk size in words
            overlap: Number of overlapping words between chunks
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        chunks = []
        
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        current_chunk = []
        current_word_count = 0
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Count words (handles both Arabic and English)
            word_count = len(re.findall(r'\S+', para))
            
            # If single paragraph exceeds max, split it
            if word_count > max_chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    metadata = self._extract_chunk_metadata(chunk_text, language)
                    chunks.append({
                        'chunk_index': chunk_index,
                        'content': chunk_text,
                        **metadata
                    })
                    chunk_index += 1
                    current_chunk = []
                    current_word_count = 0
                
                # Split long paragraph into sentences
                sentences = self._split_into_sentences(para, language)
                temp_chunk = []
                temp_word_count = 0
                
                for sentence in sentences:
                    sentence_words = len(re.findall(r'\S+', sentence))
                    
                    if temp_word_count + sentence_words > max_chunk_size and temp_chunk:
                        # Save accumulated sentences
                        chunk_text = ' '.join(temp_chunk)
                        metadata = self._extract_chunk_metadata(chunk_text, language)
                        chunks.append({
                            'chunk_index': chunk_index,
                            'content': chunk_text,
                            **metadata
                        })
                        chunk_index += 1
                        
                        # Keep last sentence for overlap
                        if overlap > 0:
                            temp_chunk = temp_chunk[-1:]
                            temp_word_count = len(re.findall(r'\S+', temp_chunk[0]))
                        else:
                            temp_chunk = []
                            temp_word_count = 0
                    
                    temp_chunk.append(sentence)
                    temp_word_count += sentence_words
                
                # Save remaining sentences
                if temp_chunk:
                    chunk_text = ' '.join(temp_chunk)
                    metadata = self._extract_chunk_metadata(chunk_text, language)
                    chunks.append({
                        'chunk_index': chunk_index,
                        'content': chunk_text,
                        **metadata
                    })
                    chunk_index += 1
            
            # Add paragraph to current chunk
            elif current_word_count + word_count > max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                metadata = self._extract_chunk_metadata(chunk_text, language)
                chunks.append({
                    'chunk_index': chunk_index,
                    'content': chunk_text,
                    **metadata
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                if overlap > 0 and current_chunk:
                    current_chunk = [current_chunk[-1], para]
                    current_word_count = len(re.findall(r'\S+', current_chunk[0])) + word_count
                else:
                    current_chunk = [para]
                    current_word_count = word_count
            else:
                current_chunk.append(para)
                current_word_count += word_count
        
        # Save final chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            metadata = self._extract_chunk_metadata(chunk_text, language)
            chunks.append({
                'chunk_index': chunk_index,
                'content': chunk_text,
                **metadata
            })
        
        logger.info(f"Created {len(chunks)} chunks from document")
        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on multiple newlines
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_into_sentences(self, text: str, language: str) -> List[str]:
        """
        Split text into sentences based on language.
        
        Args:
            text: Text to split
            language: Language code
            
        Returns:
            List of sentences
        """
        if language == 'ar':
            # Arabic sentence endings
            sentences = re.split(r'[.؟!]\s+', text)
        else:
            # English/French sentence endings
            sentences = re.split(r'[.!?]\s+', text)
        
        return [s.strip() for s in sentences if s.strip()]

    def _extract_chunk_metadata(
        self,
        chunk_text: str,
        language: str
    ) -> Dict[str, any]:
        """
        Extract metadata from chunk text.
        
        Args:
            chunk_text: Text content of the chunk
            language: Document language
            
        Returns:
            Dictionary with article_number, section_title, and keywords
        """
        metadata = {
            'article_number': None,
            'section_title': None,
            'keywords': []
        }
        
        # Detect article numbers
        if language == 'ar':
            article_match = re.search(self.ARABIC_ARTICLE_PATTERN, chunk_text)
            section_match = re.search(self.ARABIC_SECTION_PATTERN, chunk_text)
        else:
            article_match = re.search(self.ENGLISH_ARTICLE_PATTERN, chunk_text, re.IGNORECASE)
            section_match = re.search(self.ENGLISH_SECTION_PATTERN, chunk_text, re.IGNORECASE)
        
        if article_match:
            metadata['article_number'] = article_match.group(1)
        
        if section_match:
            metadata['section_title'] = section_match.group(0)
        
        # Extract keywords (simple approach - most frequent meaningful words)
        metadata['keywords'] = self._extract_keywords(chunk_text, language)
        
        return metadata

    def _extract_keywords(self, text: str, language: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            language: Language code
            max_keywords: Maximum number of keywords
            
        Returns:
            List of keywords
        """
        # Arabic stop words
        arabic_stop_words = {
            'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'ذلك', 'التي', 'الذي',
            'أن', 'أو', 'و', 'ف', 'ب', 'ل', 'ك', 'ما', 'لا', 'نعم', 'لكن'
        }
        
        # English stop words
        english_stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might'
        }
        
        stop_words = arabic_stop_words if language == 'ar' else english_stop_words
        
        # Extract words
        words = re.findall(r'\S+', text.lower())
        
        # Filter and count
        word_freq = {}
        for word in words:
            # Remove punctuation
            word = re.sub(r'[^\w\u0600-\u06FF]', '', word)
            if len(word) > 2 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords

    async def detect_document_language(self, text: str) -> str:
        """
        Detect the language of the document.
        
        Args:
            text: Sample text from document
            
        Returns:
            Language code (ar, en, fr)
        """
        # Simple language detection based on character sets
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(re.findall(r'\w', text))
        
        if total_chars == 0:
            return 'en'
        
        arabic_ratio = arabic_chars / total_chars
        
        if arabic_ratio > 0.3:
            return 'ar'
        else:
            return 'en'

    async def validate_file_format(self, file_path: str, allowed_extensions: List[str]) -> bool:
        """
        Validate if file format is supported.
        
        Args:
            file_path: Path to the file
            allowed_extensions: List of allowed extensions
            
        Returns:
            True if valid, False otherwise
        """
        file_extension = Path(file_path).suffix.lower()
        return file_extension in allowed_extensions

