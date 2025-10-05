"""
Enhanced Arabic PDF Text Extraction Service

This service integrates the advanced Arabic PDF extraction logic from extract_arabic_pdf.py
into the legal assistant system to ensure proper Arabic text extraction.

Features:
- Advanced Arabic text detection and fixing
- Comprehensive Unicode artifact cleaning
- Fragmented text normalization
- RTL direction handling
- Multi-method extraction (Direct + OCR)
- Intelligent method selection based on Arabic content quality
"""

import logging
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import arabic_reshaper
from bidi.algorithm import get_display
import re
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedArabicPDFProcessor:
    """
    Enhanced Arabic PDF processor with advanced text extraction and fixing capabilities.
    
    Integrates the sophisticated logic from extract_arabic_pdf.py for optimal Arabic text extraction.
    """

    def __init__(self):
        """Initialize the enhanced Arabic PDF processor."""
        # Configure Tesseract if available
        try:
            import os
            tesseract_cmd = os.getenv('TESSERACT_CMD', 'tesseract')
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        except Exception as e:
            logger.warning(f"Tesseract configuration warning: {e}")

    # ==================== ARABIC TEXT DETECTION & FIXING ====================

    def needs_fixing(self, text: str) -> bool:
        """
        Enhanced detection of Arabic text that needs fixing - ALWAYS fix Arabic text in PDFs
        
        From extract_arabic_pdf.py - comprehensive Arabic text detection logic.
        """
        if not text.strip():
            return False

        # Check for any Arabic characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars == 0:
            return False

        # Check for fragmented words (average word length <= 2)
        words = text.split()
        if words:
            avg_word_len = sum(len(w) for w in words) / len(words)
            if avg_word_len <= 2:
                return True

        # Check for fragmented individual Arabic characters
        fragmented_patterns = [
            len(word) == 1 and '\u0600' <= word <= '\u06FF' for word in words
        ]
        if any(fragmented_patterns):
            return True

        # Check for artifacts (isolated Unicode characters)
        artifacts = ['ﻢ', 'ﻪ', 'ﻆ', 'ﺍ', 'ﺕ', 'ﺏ', 'ﻞ', 'ﺝ', 'ﺡ', 'ﺥ', 'ﺩ', 'ﺫ', 'ﺭ', 'ﺯ', 'ﺱ', 'ﺵ', 'ﺹ', 'ﺽ', 'ﻁ', 'ﻅ', 'ﻉ', 'ﻍ', 'ﻑ', 'ﻕ', 'ﻙ', 'ﻝ', 'ﻡ', 'ﻥ', 'ﻩ', 'ﻭ', 'ﻱ']
        if any(artifact in text for artifact in artifacts):
            return True

        # For PDFs, ALWAYS apply fixing if Arabic text is detected (it may look good but still need reshaping)
        arabic_ratio = arabic_chars / len(text.strip()) if text.strip() else 0
        if arabic_ratio > 0.1:  # If 10% or more Arabic characters, fix it
            return True

        return False

    def fix_arabic_text(self, text: str) -> str:
        """
        Comprehensive Arabic text fixing with proper RTL handling
        
        From extract_arabic_pdf.py - advanced Arabic text processing.
        """
        if not text.strip():
            return text
        
        # Step 1: Clean Unicode artifacts first
        cleaned_text = self.clean_text_artifacts(text)
        
        # Step 2: Normalize fragmented text - merge broken letters into words
        normalized = self.normalize_fragmented_arabic(cleaned_text)
        
        # Step 3: Ensure proper word spacing for RTL
        words = normalized.split()
        fixed_words = []
        
        for word in words:
            # Check if word contains Arabic characters
            arabic_chars = sum(1 for c in word if '\u0600' <= c <= '\u06FF')
            if arabic_chars > 0:
                # Apply reshaping to Arabic words
                reshaped_word = arabic_reshaper.reshape(word)
                fixed_words.append(reshaped_word)
            else:
                # Keep non-Arabic words as-is
                fixed_words.append(word)
        
        # Step 4: Join words and apply BiDi algorithm for proper RTL/LTR display
        text_for_bidi = ' '.join(fixed_words)
        
        # Apply BiDi algorithm with proper base direction for Arabic text
        try:
            # Check if Arabic content dominates the text
            arabic_ratio = sum(1 for c in text_for_bidi if '\u0600' <= c <= '\u06FF') / len(text_for_bidi.strip()) if text_for_bidi.strip() else 0
            
            if arabic_ratio > 0.5:  # More than 50% Arabic
                # Prepend RTL mark for proper Arabic text direction
                rtl_text = '\u202F' + text_for_bidi + '\u202F'  # Use Narrow No-Black Space
                fixed_text = get_display(rtl_text)
            else:
                # Mixed content - use default BiDi processing
                fixed_text = get_display(text_for_bidi)
                
        except Exception as e:
            logger.warning(f"RTL processing error: {e}")
            # Fallback: just apply reshaping without BiDi
            fixed_text = text_for_bidi
        
        return fixed_text

    def ensure_rtl_text_direction(self, text: str) -> str:
        """
        Ensure Arabic text is displayed in proper RTL direction
        
        From extract_arabic_pdf.py - RTL direction handling.
        """
        if not text.strip():
            return text
        
        # Check if text contains Arabic characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars == 0:
            return text
        
        # Split text into lines and process each line
        lines = text.split('\n')
        rtl_lines = []
        
        for line in lines:
            if line.strip() and arabic_chars > 0:
                # Split line into words and process each word
                words = line.split()
                processed_words = []
                
                for word in words:
                    # Check if word contains Arabic
                    word_arabic_chars = sum(1 for c in word if '\u0600' <= c <= '\u06FF')
                    if word_arabic_chars > 0:
                        # For Arabic words, apply RTL mark
                        processed_word = '\u200F' + word + '\u200F'
                        processed_words.append(processed_word)
                    else:
                        processed_words.append(word)
                
                # Rejoin words and add RTL mark to the entire line
                processed_line = '\u202E' + ' '.join(processed_words) + '\u202C'
                rtl_lines.append(processed_line)
            else:
                rtl_lines.append(line)
        
        return '\n'.join(rtl_lines)

    def normalize_fragmented_arabic(self, text: str) -> str:
        """
        Merge fragmented Arabic letters back into words
        
        From extract_arabic_pdf.py - fragmented text normalization.
        """
        if not text.strip():
            return text
        
        # First, try to merge isolated Arabic characters that are separated by spaces
        # Split by spaces and analyze each token
        words = text.split()
        current_word = ""
        normalized_words = []
        
        for i, word in enumerate(words):
            word_clean = word.strip()
            
            if not word_clean:
                continue
                
            # If this is a single Arabic character
            if len(word_clean) == 1 and '\u0600' <= word_clean <= '\u06FF':
                # Merge with current_word if it's building an Arabic word
                if current_word and '\u0600' <= current_word[-1] <= '\u06FF':
                    current_word += word_clean
                else:
                    if current_word:
                        normalized_words.append(current_word)
                    current_word = word_clean
            
            # If this is a number or English, separate it
            elif word_clean.isdigit() or word_clean.isalpha() or word_clean in ['.', ',', ':', ';']:
                if current_word:
                    normalized_words.append(current_word)
                    current_word = ""
                normalized_words.append(word_clean)
            
            # If this is a longer word that contains Arabic
            else:
                arabic_chars = sum(1 for c in word_clean if '\u0600' <= c <= '\u06FF')
                if arabic_chars > len(word_clean) * 0.7:  # Mostly Arabic word
                    if current_word and '\u0600' <= current_word[-1] <= '\u06FF':
                        current_word += word_clean
                    else:
                        if current_word:
                            normalized_words.append(current_word)
                            current_word = ""
                        current_word = word_clean
                else:  # Non-Arabic word
                    if current_word:
                        normalized_words.append(current_word)
                        current_word = ""
                    normalized_words.append(word_clean)
        
        # Add any remaining word
        if current_word:
            normalized_words.append(current_word)
        
        # Clean up artifacts and excessive spaces
        normalized_text = ' '.join(normalized_words)
        normalized_text = self.clean_text_artifacts(normalized_text)
        
        return normalized_text

    def clean_text_artifacts(self, text: str) -> str:
        """
        Remove artifacts and clean up text formatting
        
        From extract_arabic_pdf.py - comprehensive Unicode artifact cleaning.
        """
        if not text:
            return text
        
        # Remove excessive spaces
        text = ' '.join(text.split())
        
        # Comprehensive Arabic Unicode artifact cleaning
        # Convert various Unicode forms to standard Arabic letters
        
        # Isolated forms to standard forms
        artifacts_map = {
            # Alef forms
            'ﺍ': 'ا', 'ﺎ': 'ا', 'ﺀ': 'ء', 'ﺃ': 'أ', 'ﺄ': 'أ', 'ﺇ': 'إ', 'ﺈ': 'إ', 'ﺅ': 'ؤ', 'ﺆ': 'ؤ',
            
            # Ba forms  
            'ﺏ': 'ب', 'ﺐ': 'ب', 'ﺑ': 'ب', 'ﺒ': 'ب',
            
            # Ta forms
            'ﺕ': 'ت', 'ﺖ': 'ت', 'ﺗ': 'ت', 'ﺘ': 'ت', 'ﺙ': 'ث', 'ﺚ': 'ث', 'ﺛ': 'ث', 'ﺜ': 'ث',
            
            # Dal forms
            'ﺩ': 'د', 'ﺪ': 'د', 'ﺫ': 'ذ', 'ﺬ': 'ذ',
            
            # Ra forms
            'ﺭ': 'ر', 'ﺮ': 'ر', 'ﺯ': 'ز', 'ﺰ': 'ز',
            
            # Seen forms
            'ﺱ': 'س', 'ﺲ': 'س', 'ﺳ': 'س', 'ﺴ': 'س', 'ﺵ': 'ش', 'ﺶ': 'ش', 'ﺷ': 'ش', 'ﺸ': 'ش',
            
            # Sad forms
            'ﺹ': 'ص', 'ﺺ': 'ص', 'ﺻ': 'ص', 'ﺼ': 'ص', 'ﺽ': 'ض', 'ﺾ': 'ض', 'ﺿ': 'ض', 'ﻀ': 'ض',
            
            # Ta forms (different types)
            'ﻁ': 'ط', 'ﻂ': 'ط', 'ﻃ': 'ط', 'ﻄ': 'ط', 'ﻅ': 'ظ', 'ﻆ': 'ظ', 'ﻈ': 'ظ', 'ﻇ': 'ظ',
            
            # Ain forms
            'ﻉ': 'ع', 'ﻊ': 'ع', 'ﻋ': 'ع', 'ﻌ': 'ع', 'ﻍ': 'غ', 'ﻎ': 'غ', 'ﻏ': 'غ', 'ﻐ': 'غ',
            
            # Fa forms
            'ﻑ': 'ف', 'ﻒ': 'ف', 'ﻓ': 'ف', 'ﻔ': 'ف', 'ﻕ': 'ق', 'ﻖ': 'ق', 'ﻗ': 'ق', 'ﻘ': 'ق',
            
            # Kaf forms
            'ﻙ': 'ك', 'ﻚ': 'ك', 'ﻛ': 'ك', 'ﻜ': 'ك',
            
            # Lam forms
            'ﻝ': 'ل', 'ﻞ': 'ل', 'ﻟ': 'ل', 'ﻠ': 'ل', 'ﻡ': 'م', 'ﻢ': 'م', 'ﻣ': 'م', 'ﻤ': 'م',
            
            # Noon forms
            'ﻥ': 'ن', 'ﻦ': 'ن', 'ﻧ': 'ن', 'ﻨ': 'ن', 'ﻩ': 'ه', 'ﻪ': 'ه', 'ﻫ': 'ه', 'ﻬ': 'ه',
            
            # Waw forms
            'ﻭ': 'و', 'ﻮ': 'و', 'ﺩ': 'د', 'ﺪ': 'د', 'ﺰ': 'ز', 'ﺯ': 'ز',
            
            # Ya forms
            'ﻱ': 'ي', 'ﻲ': 'ي', 'ﻳ': 'ي', 'ﻴ': 'ي', 'ﺀ': 'ء', 'ﺁ': 'آ', 'ﺂ': 'آ',
            
            # Additional artifacts
            'ﻼ': 'لا', 'ﻻ': 'لا', 'ﺒ': 'ب', 'ﺑ': 'ب', 'ﺔ': 'ة', 'ﺓ': 'ة',
        }
        
        # Apply character mapping
        for artifact, correct_char in artifacts_map.items():
            text = text.replace(artifact, correct_char)
        
        # Clean up any remaining isolated Arabic forms that might have been missed
        # Remove any remaining isolated Unicode forms (Unicode range U+FE70-U+FEFC)
        text = re.sub(r'[\uFE70-\uFEFC]', lambda m: artifacts_map.get(m.group(), m.group()), text)
        
        return text

    # ==================== PDF TEXT EXTRACTION ====================

    def extract_text_direct(self, pdf_path: str) -> str:
        """
        Direct text extraction using PyMuPDF with advanced Arabic processing
        
        From extract_arabic_pdf.py - sophisticated direct extraction logic.
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num, page in enumerate(doc, 1):
                try:
                    logger.info(f"Processing page {page_num} with dict extraction...")
                    
                    # Use get_text("dict") to get all possible text
                    page_dict = page.get_text("dict")
                    
                    if not page_dict or "blocks" not in page_dict:
                        logger.warning(f"No dict blocks found at page {page_num}")
                        text += f"\n---EMPTY_PAGE_{page_num}---\n"
                        continue
                    
                    blocks = page_dict["blocks"]
                    logger.info(f"Page {page_num}: Found {len(blocks)} blocks in dict")
                    
                    # Process each block individually - full depth: blocks -> lines -> spans
                    for block_num, block in enumerate(blocks):
                        if "lines" not in block:
                            logger.warning(f"Block {block_num} at page {page_num} has no lines")
                            text += "\n"  # Keep separator
                            continue
                        
                        lines = block["lines"]
                        logger.debug(f"Page {page_num}, Block {block_num}: Found {len(lines)} lines")
                        
                        # Process each line individually
                        for line_num, line in enumerate(lines):
                            if "spans" not in line:
                                logger.warning(f"Line {line_num} in block {block_num} at page {page_num} has no spans")
                                text += "\n"  # Keep empty line
                                continue
                            
                            spans = line["spans"]
                            line_text = ""
                            
                            # Extract each span individually
                            for span_num, span in enumerate(spans):
                                if "text" not in span:
                                    logger.warning(f"Span {span_num} in line {line_num}, block {block_num}, page {page_num} has no text")
                                    continue
                                
                                span_text = span["text"]
                                if not span_text.strip():
                                    logger.warning(f"Empty span {span_num} in line {line_num}, block {block_num}, page {page_num}")
                                    line_text += " "  # Keep space
                                    continue
                                
                                logger.debug(f"Page {page_num}, Block {block_num}, Line {line_num}, Span {span_num}: '{span_text[:30]}...'")
                                line_text += span_text
                            
                            # Apply fix_arabic_text to each line (always) - don't ignore any text
                            if line_text.strip():
                                # Always apply Arabic fixing and RTL direction for any Arabic content
                                if self.needs_fixing(line_text):
                                    fixed_line = self.fix_arabic_text(line_text)
                                    # Apply RTL direction for Arabic text
                                    fixed_line = self.ensure_rtl_text_direction(fixed_line)
                                    logger.debug(f"Fixed Arabic line: '{line_text[:30]}...' -> '{fixed_line[:30]}...'")
                                else:
                                    # Check if line contains Arabic and needs RTL direction
                                    fixed_line = self.ensure_rtl_text_direction(line_text)
                                text += fixed_line + "\n"
                            else:
                                logger.warning(f"Empty line {line_num} in block {block_num} at page {page_num}")
                                text += "\n"  # Keep empty line to preserve structure
                    
                    # Add page separator
                    text += "\n---PAGE_SEPARATOR---\n"
                    
                except Exception as page_e:
                    logger.error(f"Error processing page {page_num}: {page_e}")
                    text += f"\n---ERROR_PAGE_{page_num}---\n"
                    continue
            
            doc.close()
            logger.info(f"[Direct] Extracted {len(text)} characters from {len(doc)} pages using dict extraction")
            return text
            
        except Exception as e:
            logger.error(f"Direct extraction failed: {e}")
            return ""

    def extract_text_ocr(self, pdf_path: str, language: str = 'ar') -> str:
        """
        OCR-based extraction using pdf2image + Tesseract with advanced Arabic processing
        
        From extract_arabic_pdf.py - sophisticated OCR extraction logic.
        """
        try:
            # Map language codes for OCR
            lang_map = {
                'ar': 'ara',
                'en': 'eng',
                'fr': 'fra'
            }
            tesseract_lang = lang_map.get(language, 'ara')
            
            pages = convert_from_path(pdf_path, dpi=300)
            text = ""
            
            for page_num, page in enumerate(pages, 1):
                try:
                    logger.info(f"OCR processing page {page_num}/{len(pages)}...")
                    
                    # Use --psm 4 as default (single column) instead of --psm 6
                    raw_page_text = pytesseract.image_to_string(
                        page, lang=tesseract_lang, config="--oem 3 --psm 4"
                    )
                    
                    # If no text extracted, try --psm 11 (sparse text)
                    if not raw_page_text.strip():
                        logger.warning(f"No text with --psm 4 from page {page_num}, trying --psm 11...")
                        raw_page_text = pytesseract.image_to_string(
                            page, lang=tesseract_lang, config="--oem 3 --psm 11"
                        )
                    
                    if not raw_page_text.strip():
                        logger.warning(f"No OCR text extracted from page {page_num} with any PSM")
                        text += f"\n---NO_OCR_PAGE_{page_num}---\n"
                        text += "\n---PAGE_SEPARATOR---\n"
                        continue
                    
                    logger.info(f"Page {page_num} raw OCR: {len(raw_page_text)} characters")
                    
                    # Split text into lines - keep every line
                    ocr_lines = raw_page_text.splitlines()
                    logger.info(f"Page {page_num}: Found {len(ocr_lines)} lines from OCR")
                    
                    # Process each line individually - don't ignore anything
                    for line_num, line in enumerate(ocr_lines):
                        if not line.strip():
                            logger.warning(f"Empty OCR line {line_num} at page {page_num}")
                            text += "\n"  # Keep empty line
                            continue
                        
                        # Print debug for raw content
                        logger.debug(f"Page {page_num}, Line {line_num}: '{line[:50]}...'")
                        
                        # Apply fix_arabic_text to each line - OCR always needs fixing for Arabic texts
                        if self.needs_fixing(line):
                            fixed_line = self.fix_arabic_text(line)
                            # Apply RTL direction for OCR Arabic text
                            fixed_line = self.ensure_rtl_text_direction(fixed_line)
                            logger.debug(f"Fixed OCR line: '{line[:30]}...' -> '{fixed_line[:30]}...'")
                        else:
                            # Check if OCR line contains Arabic and needs RTL direction
                            fixed_line = self.ensure_rtl_text_direction(line)
                        text += fixed_line + "\n"
                    
                    # Add page separator
                    text += "\n---PAGE_SEPARATOR---\n"
                    
                except Exception as page_e:
                    logger.error(f"Error processing OCR page {page_num}: {page_e}")
                    # Even if page fails, try to continue
                    text += f"\n---ERROR_PAGE_{page_num}---\n"
                    text += "\n---PAGE_SEPARATOR---\n"
                    continue
            
            logger.info(f"[OCR] Extracted {len(text)} characters from {len(pages)} pages using improved PSM")
            return text
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    def extract_pdf_text(self, pdf_path: str, language: str = 'ar') -> Tuple[str, str]:
        """
        Extract text from PDF using the best method available.
        
        Combines direct extraction and OCR, then selects the best result based on Arabic content quality.
        
        Args:
            pdf_path: Path to the PDF file
            language: Document language ('ar', 'en', 'fr')
            
        Returns:
            Tuple of (extracted_text, method_used)
        """
        logger.info(f"Starting enhanced PDF extraction for: {pdf_path}")
        
        # 1. Try Direct Extraction first
        logger.info("=== Starting Direct Text Extraction ===")
        direct_text = self.extract_text_direct(pdf_path)
        
        # Count characters and Arabic content for assessment
        direct_chars = len(direct_text)
        direct_arabic_chars = sum(1 for c in direct_text if '\u0600' <= c <= '\u06FF')
        
        # 2. Try OCR Extraction as backup/complement
        logger.info("=== Starting OCR Text Extraction ===")
        ocr_text = self.extract_text_ocr(pdf_path, language)
        
        # Count characters and Arabic content for assessment
        ocr_chars = len(ocr_text)
        ocr_arabic_chars = sum(1 for c in ocr_text if '\u0600' <= c <= '\u06FF')
        
        # Choose the best result (more Arabic content is better for legal documents)
        if ocr_arabic_chars > direct_arabic_chars:
            logger.info(f"OCR extraction yielded more Arabic content ({ocr_arabic_chars} vs {direct_arabic_chars} chars)")
            best_text = ocr_text
            best_method = "OCR"
        else:
            logger.info(f"Direct extraction yielded more Arabic content ({direct_arabic_chars} vs {ocr_arabic_chars} chars)")
            best_text = direct_text
            best_method = "Direct"
        
        logger.info(f"Extraction finished!")
        logger.info(f"Direct: {direct_chars} chars ({direct_arabic_chars} Arabic)")
        logger.info(f"OCR: {ocr_chars} chars ({ocr_arabic_chars} Arabic)")
        logger.info(f"Best method: {best_method}")
        
        return best_text, best_method

    def process_extracted_text(self, text: str) -> dict:
        """
        Process extracted text and return comprehensive analysis.
        
        Args:
            text: Extracted text to process
            
        Returns:
            Dictionary with processed text and metadata
        """
        if not text or not text.strip():
            return {
                'processed_text': '',
                'original_text': text,
                'arabic_chars': 0,
                'total_chars': 0,
                'arabic_ratio': 0.0,
                'needs_fixing': False,
                'rtl_applied': False,
                'artifacts_cleaned': False
            }
        
        # Analyze original text
        original_arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        original_total_chars = len(text)
        original_arabic_ratio = original_arabic_chars / original_total_chars if original_total_chars > 0 else 0
        
        # Process text
        processed_text = text
        artifacts_cleaned = False
        needs_fixing_applied = False
        rtl_applied = False
        
        # Clean artifacts
        if any(artifact in text for artifact in ['ﻢ', 'ﻪ', 'ﻆ', 'ﺍ', 'ﺕ', 'ﺏ', 'ﻞ', 'ﺝ', 'ﺡ', 'ﺥ', 'ﺩ', 'ﺫ', 'ﺭ', 'ﺯ', 'ﺱ', 'ﺵ', 'ﺹ', 'ﺽ', 'ﻁ', 'ﻅ', 'ﻉ', 'ﻍ', 'ﻑ', 'ﻕ', 'ﻙ', 'ﻝ', 'ﻡ', 'ﻥ', 'ﻩ', 'ﻭ', 'ﻱ']):
            processed_text = self.clean_text_artifacts(processed_text)
            artifacts_cleaned = True
        
        # Apply Arabic fixing if needed
        if self.needs_fixing(processed_text):
            processed_text = self.fix_arabic_text(processed_text)
            needs_fixing_applied = True
        
        # Apply RTL direction
        if original_arabic_chars > 0:
            processed_text = self.ensure_rtl_text_direction(processed_text)
            rtl_applied = True
        
        # Analyze processed text
        processed_arabic_chars = sum(1 for c in processed_text if '\u0600' <= c <= '\u06FF')
        processed_total_chars = len(processed_text)
        processed_arabic_ratio = processed_arabic_chars / processed_total_chars if processed_total_chars > 0 else 0
        
        return {
            'processed_text': processed_text,
            'original_text': text,
            'arabic_chars': processed_arabic_chars,
            'total_chars': processed_total_chars,
            'arabic_ratio': processed_arabic_ratio,
            'needs_fixing': needs_fixing_applied,
            'rtl_applied': rtl_applied,
            'artifacts_cleaned': artifacts_cleaned,
            'improvement': {
                'arabic_chars_increase': processed_arabic_chars - original_arabic_chars,
                'total_chars_change': processed_total_chars - original_total_chars,
                'arabic_ratio_change': processed_arabic_ratio - original_arabic_ratio
            }
        }
