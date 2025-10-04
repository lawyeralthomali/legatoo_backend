"""
Enhanced Document Processing Service - Phase 3 Implementation

This service handles:
- Multi-format document conversion (PDF, DOCX, Images)
- OCR for images using Tesseract
- Advanced text cleaning and normalization
- Intelligent chunking (300-500 words)
- Legal entity extraction (articles, sections)

Supports: PDF, DOCX, DOC, TXT, JPG, PNG, TIFF
"""

import re
import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import asyncio

# Document processing libraries
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from docx import Document as DocxDocument
from PIL import Image

# Arabic text processing
import arabic_reshaper
from bidi.algorithm import get_display
from ..utils.arabic_text_processor import ArabicTextProcessor

logger = logging.getLogger(__name__)


class EnhancedDocumentProcessor:
    """
    Enhanced document processor with OCR support and advanced text cleaning.
    
    Phase 3 Implementation:
    - Supports PDF, DOCX, and image files (OCR)
    - Advanced text cleaning and normalization
    - Intelligent chunking (300-500 words)
    - Legal entity detection
    """

    # Legal patterns for Arabic and English
    ARABIC_ARTICLE_PATTERN = r'(?:المادة|الماده|مادة)\s*(?:رقم)?\s*(\d+|[٠-٩]+)'
    ARABIC_SECTION_PATTERN = r'(?:الباب|الفصل|القسم)\s*(?:ال)?(\w+)'
    ENGLISH_ARTICLE_PATTERN = r'(?:Article|Section|Clause)\s+(?:No\.?\s*)?(\d+)'
    ENGLISH_SECTION_PATTERN = r'(?:Chapter|Part|Section)\s+(\w+)'

    # File type support
    PDF_EXTENSIONS = ['.pdf']
    WORD_EXTENSIONS = ['.docx', '.doc']
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']
    TEXT_EXTENSIONS = ['.txt']

    def __init__(self):
        """Initialize the enhanced document processor."""
        self.tesseract_cmd = os.getenv('TESSERACT_CMD', 'tesseract')
        try:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        except:
            logger.warning("Tesseract not configured. OCR will not work.")

    # ==================== ARABIC TEXT PROCESSING ====================

    def needs_fixing(self, text: str) -> bool:
        """
        Determine if Arabic text needs fixing (reshape + bidi).
        
        Simple rule: if the text has disconnected Arabic characters 
        (spaces between each character) or clear reversed direction → needs fixing.
        """
        if not text.strip():
            return False

        # Simple heuristic: if average word length is very short → likely broken
        words = text.split()
        avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
        return avg_word_len <= 2  # If words are very short (≤2 chars) → likely broken

    def fix_arabic_text(self, text: str) -> str:
        """Apply reshape + bidi to Arabic text."""
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception as e:
            logger.warning(f"Arabic text fixing failed: {e}")
            return text

    # ==================== PHASE 3: FILE CONVERSION ====================

    async def extract_text_from_file(
        self,
        file_path: str,
        file_extension: str,
        language: str = 'ar'
    ) -> str:
        """
        Extract text from any supported file format.
        
        Phase 3: Multi-format support with OCR
        
        Args:
            file_path: Path to the file
            file_extension: File extension (.pdf, .docx, .jpg, etc.)
            language: Document language for OCR (ar, en)
            
        Returns:
            Extracted and cleaned text
            
        Raises:
            ValueError: If file format is unsupported
        """
        try:
            file_ext = file_extension.lower()
            
            # PDF files
            if file_ext in self.PDF_EXTENSIONS:
                return await self._extract_from_pdf(file_path, language)
            
            # Word documents
            elif file_ext in self.WORD_EXTENSIONS:
                return await self._extract_from_docx(file_path)
            
            # Images (OCR)
            elif file_ext in self.IMAGE_EXTENSIONS:
                return await self._extract_from_image(file_path, language)
            
            # Text files
            elif file_ext in self.TEXT_EXTENSIONS:
                return await self._extract_from_txt(file_path)
            
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise

    async def _extract_from_pdf(self, file_path: str, language: str = 'ar') -> str:
        """
        Enhanced PDF extraction optimized for Arabic text.
        
        Uses your approach from extract_arabic_pdf.py:
        1. Direct extraction with PyMuPDF (fitz)
        2. Falls back to OCR if direct extraction fails or produces poor results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_pdf_sync, file_path, language)

    def _extract_pdf_sync(self, file_path: str, language: str = 'ar') -> str:
        """
        Synchronous PDF extraction optimized for Arabic.
        
        Enhanced extraction strategy:
        1. Direct extraction using PyMuPDF (fitz) for better Arabic support
        2. Optional OCR fallback for scanned documents
        3. Arabic text fixing when needed
        """
        logger.info("Starting PDF extraction with enhanced Arabic support...")
        
        # Try direct extraction first
        direct_text = self._extract_text_direct(file_path)
        
        # If direct extraction produced good results, use it
        if direct_text and len(direct_text.strip()) > 100:
            logger.info(f"[Direct] Extracted {len(direct_text)} characters successfully")
            return direct_text
        
        # Fallback to OCR if direct extraction failed or produced poor results
        logger.info("Direct extraction insufficient, trying OCR...")
        ocr_text = self._extract_text_ocr(file_path, language)
        
        if ocr_text and len(ocr_text.strip()) > 50:
            logger.info(f"[OCR] Extracted {len(ocr_text)} characters")
            return ocr_text
        
        # If both fail, try traditional methods as last resort
        logger.warning("Both direct and OCR extraction failed, trying fallback methods...")
        return self._extract_pdf_fallback(file_path)

    def _extract_text_direct(self, pdf_path: str) -> str:
        """
        Direct text extraction using PyMuPDF (fitz) - optimized for Arabic.
        
        From your extract_arabic_pdf.py implementation.
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page in doc:
                # Use "blocks" extraction for better Arabic results
                page_text = page.get_text("blocks")
                if page_text:
                    blocks_text = "\n".join([block[4] for block in page_text if block[4].strip()])
                    if blocks_text.strip():
                        text += blocks_text + "\n"
            
            doc.close()
            
            # If text needs fixing (disconnected Arabic chars), fix it
            if self.needs_fixing(text):
                text = self.fix_arabic_text(text)
            
            return text
            
        except Exception as e:
            logger.error(f"Direct extraction failed: {e}")
            return ""

    def _extract_text_ocr(self, pdf_path: str, language: str = 'ar') -> str:
        """
        OCR-based extraction using pdf2image + Tesseract - for scanned PDFs.
        
        From your extract_arabic_pdf.py implementation.
        """
        try:
            # Map language codes for OCR
            lang_map = {
                'ar': 'ara',
                'en': 'eng',
                'fr': 'fra'
            }
            tesseract_lang = lang_map.get(language, 'ara')
            
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=300)
            text = ""
            
            for i, page in enumerate(pages):
                logger.info(f"OCR processing page {i+1}/{len(pages)}...")
                
                page_text = pytesseract.image_to_string(
                    page, 
                    lang=tesseract_lang, 
                    config="--oem 3 --psm 6"  # Optimized for Arabic documents
                )
                
                # Fix Arabic text if needed
                if page_text and self.needs_fixing(page_text):
                    page_text = self.fix_arabic_text(page_text)
                
                text += page_text + "\n"
            
            return text
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    def _extract_pdf_fallback(self, file_path: str) -> str:
        """
        Fallback PDF extraction using pdfplumber and PyPDF2.
        
        Traditional extraction methods as last resort.
        """
        text_content = []
        
        try:
            # Try pdfplumber first
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            text_content.append(text)
                    except Exception as e:
                        logger.warning(f"pdfplumber failed on page {page_num}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {str(e)}")
            
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            text = page.extract_text()
                            if text and text.strip():
                                text_content.append(text)
                        except Exception as e:
                            logger.warning(f"PyPDF2 failed on page {page_num}: {str(e)}")
                            continue
                            
            except Exception as e2:
                logger.error(f"All PDF extraction methods failed: {str(e2)}")
                raise ValueError(f"Could not extract text from {file_path}")
        
        return '\n\n'.join(text_content)

    async def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_docx_sync, file_path)

    def _extract_docx_sync(self, file_path: str) -> str:
        """Synchronous DOCX extraction."""
        document = DocxDocument(file_path)
        paragraphs = [para.text for para in document.paragraphs if para.text.strip()]
        return '\n\n'.join(paragraphs)

    async def _extract_from_image(self, file_path: str, language: str = 'ar') -> str:
        """
        Extract text from image using Tesseract OCR.
        
        Phase 3: OCR support for images
        
        Args:
            file_path: Path to image file
            language: OCR language ('ara' for Arabic, 'eng' for English)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_image_sync, file_path, language)

    def _extract_image_sync(self, file_path: str, language: str = 'ar') -> str:
        """
        Synchronous OCR extraction.
        
        Tesseract language codes:
        - 'ara' for Arabic
        - 'eng' for English
        - 'ara+eng' for mixed
        """
        try:
            # Map language codes
            lang_map = {
                'ar': 'ara',
                'en': 'eng',
                'fr': 'fra'
            }
            tesseract_lang = lang_map.get(language, 'ara')
            
            # Open image
            image = Image.open(file_path)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                image,
                lang=tesseract_lang,
                config='--psm 6'  # Assume uniform block of text
            )
            
            return text
            
        except Exception as e:
            logger.error(f"OCR failed for {file_path}: {str(e)}")
            raise ValueError(f"OCR extraction failed: {str(e)}")

    async def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file with encoding detection."""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Fallback to other encodings for Arabic text
            for encoding in ['cp1256', 'iso-8859-6', 'utf-16', 'windows-1256']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("Could not decode text file with supported encodings")

    # ==================== PHASE 3: TEXT CLEANING ====================

    async def clean_text(self, text: str, language: str = 'ar') -> str:
        """
        Clean and normalize extracted text with Arabic text processing.
        
        Phase 3: Advanced cleaning:
        - Remove duplicates
        - Remove irrelevant footers/headers
        - Normalize numbers
        - Normalize language
        - Remove excess whitespace
        - Arabic text normalization
        
        Args:
            text: Raw extracted text
            language: Text language
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # 1. Normalize line breaks
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)
        
        # 2. Remove page numbers and headers/footers
        # Common patterns: "Page 1", "صفحة ١", etc.
        text = re.sub(r'(?:Page|صفحة|ص)\s*[:\-]?\s*\d+', '', text, flags=re.IGNORECASE)
        
        # 3. Remove repeated horizontal lines
        text = re.sub(r'[-_=]{3,}', '', text)
        
        # 4. Use Arabic text processor for normalization
        if language == 'ar' and ArabicTextProcessor.is_arabic_text(text):
            # Normalize Arabic text
            text = ArabicTextProcessor.normalize_arabic_text(text)
        else:
            # Basic normalization for non-Arabic text
            text = re.sub(r' +', ' ', text)
        
        # 5. Remove duplicate spaces
        text = re.sub(r' +', ' ', text)
        
        # 6. Remove duplicate empty lines (keep max 2 line breaks)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 7. Remove duplicate sentences (simple approach)
        lines = text.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            line_stripped = line.strip()
            if line_stripped and line_stripped not in seen:
                seen.add(line_stripped)
                unique_lines.append(line)
            elif not line_stripped:  # Keep empty lines
                unique_lines.append(line)
        
        text = '\n'.join(unique_lines)
        
        # 8. Trim whitespace
        text = text.strip()
        
        logger.info(f"Text cleaned: {len(text)} characters")
        return text

    # ==================== PHASE 3: TEXT CHUNKING ====================

    async def chunk_text(
        self,
        text: str,
        language: str,
        min_chunk_size: int = 300,
        max_chunk_size: int = 500,
        overlap: int = 50
    ) -> List[Dict[str, any]]:
        """
        Split text into chunks of 300-500 words.
        
        Phase 3: Intelligent chunking with legal context preservation
        
        Args:
            text: Full document text
            language: Document language (ar, en)
            min_chunk_size: Minimum chunk size in words (default: 300)
            max_chunk_size: Maximum chunk size in words (default: 500)
            overlap: Overlapping words between chunks (default: 50)
            
        Returns:
            List of chunk dictionaries with metadata
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
                        
                        # Keep last sentences for overlap
                        if overlap > 0 and len(temp_chunk) > 1:
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
        
        logger.info(f"Created {len(chunks)} chunks (300-500 words each)")
        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_into_sentences(self, text: str, language: str) -> List[str]:
        """Split text into sentences based on language."""
        if language == 'ar':
            # Arabic sentence endings
            sentences = re.split(r'[.؟!]\s+', text)
        else:
            # English/French sentence endings
            sentences = re.split(r'[.!?]\s+', text)
        
        return [s.strip() for s in sentences if s.strip()]

    def _extract_chunk_metadata(self, chunk_text: str, language: str) -> Dict[str, any]:
        """
        Extract metadata from chunk text.
        
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
        metadata['keywords'] = self._extract_keywords(chunk_text, language, max_keywords=10)
        
        return metadata

    def _extract_keywords(self, text: str, language: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
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

    def is_supported_format(self, file_extension: str) -> bool:
        """
        Check if file format is supported.
        
        Args:
            file_extension: File extension with dot (e.g., '.pdf')
            
        Returns:
            True if supported, False otherwise
        """
        ext = file_extension.lower()
        supported = (
            self.PDF_EXTENSIONS +
            self.WORD_EXTENSIONS +
            self.IMAGE_EXTENSIONS +
            self.TEXT_EXTENSIONS
        )
        return ext in supported

