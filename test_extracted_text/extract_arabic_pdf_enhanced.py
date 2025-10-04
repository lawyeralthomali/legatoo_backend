#!/usr/bin/env python3
"""
Enhanced Arabic PDF Text Extraction Script
==========================================

A robust, reliable, and proficient script for extracting Arabic text from PDF files.
Supports both direct text extraction and OCR with intelligent text processing.

Features:
- Dual extraction methods (Direct + OCR)
- Intelligent Arabic text processing
- Quality assessment and comparison
- Comprehensive error handling
- Progress tracking and logging
- Configurable parameters
"""

import sys
import logging
import argparse
import time
from pathlib import Path
from typing import Tuple, Dict, Optional
import json

# Core libraries
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    fitz = None

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image, ImageEnhance, ImageFilter
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    pytesseract = None
    convert_from_path = None
    Image = None
    ImageEnhance = None
    ImageFilter = None

# Try to import OpenCV separately (optional)
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    np = None

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_AVAILABLE = True
except ImportError:
    ARABIC_AVAILABLE = False
    arabic_reshaper = None
    get_display = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('extraction_enhanced.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ArabicTextProcessor:
    """Enhanced Arabic text processing with quality assessment"""
    
    def __init__(self):
        self.arabic_available = ARABIC_AVAILABLE
        if not self.arabic_available:
            logger.warning("Arabic text processing libraries not available")
    
    def needs_fixing(self, text: str) -> bool:
        """
        Enhanced detection of Arabic text that needs processing.
        Uses multiple heuristics for better accuracy.
        """
        if not text.strip():
            return False
        
        # Check for Arabic characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars == 0:
            return False
        
        # Use the simple rule that works well: check average word length
        words = text.split()
        if len(words) == 0:
            return False
        
        avg_word_len = sum(len(w) for w in words) / len(words)
        
        # Multiple detection methods - simplified approach
        methods = [
            avg_word_len <= 2,  # Simple rule that works
            self._detect_broken_words(text),
            self._detect_reversed_text(text),
            self._detect_spacing_issues(text)
        ]
        
        # If any method detects issues, process the text
        return any(methods)
    
    def _detect_broken_words(self, text: str) -> bool:
        """Detect if Arabic words are broken (spaces between letters)"""
        words = text.split()
        if len(words) == 0:
            return False
        
        avg_word_len = sum(len(w) for w in words) / len(words)
        return avg_word_len <= 2
    
    def _detect_reversed_text(self, text: str) -> bool:
        """Detect if text appears to be reversed"""
        # Simple heuristic: check for common Arabic words in reverse
        arabic_words = text.split()
        if len(arabic_words) == 0:
            return False
        
        # Check if first few words look reversed
        first_words = arabic_words[:3]
        for word in first_words:
            if len(word) > 1 and word[0] in 'ءآأإؤئابتثجحخدذرزسشصضطظعغفقكلمنهوي':
                # If word starts with Arabic letter but looks reversed
                if self._looks_reversed(word):
                    return True
        return False
    
    def _detect_spacing_issues(self, text: str) -> bool:
        """Detect spacing and formatting issues"""
        lines = text.split('\n')
        if len(lines) == 0:
            return False
        
        # Check for lines with excessive spaces or unusual patterns
        for line in lines[:5]:  # Check first 5 lines
            if len(line.split()) > len(line.replace(' ', '')) / 2:
                return True
        return False
    
    def _looks_reversed(self, word: str) -> bool:
        """Simple heuristic to detect reversed Arabic words"""
        if len(word) < 2:
            return False
        
        # Check for common patterns that indicate reversed text
        return word[-1] in 'ءآأإؤئابتثجحخدذرزسشصضطظعغفقكلمنهوي' and \
               word[0] in 'ءآأإؤئابتثجحخدذرزسشصضطظعغفقكلمنهوي'
    
    def fix_arabic_text(self, text: str) -> str:
        """Arabic text fixing - use simple approach that works"""
        if not self.arabic_available or not text.strip():
            return text
        
        try:
            # Use the simple approach that works in the basic script
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
            
        except Exception as e:
            logger.error(f"Error in Arabic text processing: {e}")
            return text
    
    def _assess_text_quality(self, text: str) -> float:
        """Assess the quality of processed Arabic text"""
        if not text.strip():
            return 0.0
        
        score = 0.0
        
        # Check for proper Arabic word formation
        words = text.split()
        proper_words = 0
        for word in words:
            if len(word) >= 2 and self._is_proper_arabic_word(word):
                proper_words += 1
        
        if len(words) > 0:
            score += (proper_words / len(words)) * 0.6
        
        # Check for reasonable line length (not too fragmented)
        lines = text.split('\n')
        if lines:
            avg_line_length = sum(len(line.strip()) for line in lines) / len(lines)
            if avg_line_length > 10:  # Reasonable line length
                score += 0.4
        
        return score
    
    def _is_proper_arabic_word(self, word: str) -> bool:
        """Check if word looks like a proper Arabic word"""
        if len(word) < 2:
            return False
        
        # Simple check: proper Arabic words usually have connected letters
        arabic_chars = sum(1 for c in word if '\u0600' <= c <= '\u06FF')
        return arabic_chars >= len(word) * 0.8  # At least 80% Arabic characters

class PDFExtractor:
    """Enhanced PDF text extractor with multiple strategies"""
    
    def __init__(self, arabic_processor: ArabicTextProcessor):
        self.arabic_processor = arabic_processor
        self.fitz_available = FITZ_AVAILABLE
        self.ocr_available = OCR_AVAILABLE
    
    def extract_direct(self, pdf_path: str) -> Tuple[str, Dict]:
        """Enhanced direct text extraction with multiple methods"""
        if not self.fitz_available:
            logger.error("PyMuPDF not available for direct extraction")
            return "", {"error": "PyMuPDF not installed"}
        
        try:
            start_time = time.time()
            
            # Try each extraction method separately to avoid document closure issues
            methods_results = []
            page_count = 0
            
            # Method 1: Standard text extraction
            try:
                doc = fitz.open(pdf_path)
                page_count = len(doc)
                text_standard = ""
                for page in doc:
                    text_standard += page.get_text() + "\n"
                doc.close()
                methods_results.append(("standard", text_standard))
            except Exception as e:
                logger.warning(f"Standard extraction failed: {e}")
                methods_results.append(("standard", ""))
            
            # Method 2: Blocks extraction (often better for Arabic)
            try:
                doc = fitz.open(pdf_path)
                text_blocks = ""
                for page in doc:
                    blocks = page.get_text("blocks")
                    if blocks:
                        text_blocks += "\n".join([block[4] for block in blocks if block[4].strip()]) + "\n"
                doc.close()
                methods_results.append(("blocks", text_blocks))
            except Exception as e:
                logger.warning(f"Blocks extraction failed: {e}")
                methods_results.append(("blocks", ""))
            
            # Method 3: Words extraction
            try:
                doc = fitz.open(pdf_path)
                text_words = ""
                for page in doc:
                    words = page.get_text("words")
                    if words:
                        text_words += "\n".join([word[4] for word in words if word[4].strip()]) + "\n"
                doc.close()
                methods_results.append(("words", text_words))
            except Exception as e:
                logger.warning(f"Words extracting failed: {e}")
                methods_results.append(("words", ""))
            
            # Choose the best method based on Arabic content quality
            best_text = ""
            best_method = "standard"
            best_score = 0
            
            for method, text in methods_results:
                if self.arabic_processor.needs_fixing(text):
                    processed_text = self.arabic_processor.fix_arabic_text(text)
                else:
                    processed_text = text
                
                score = self._assess_extraction_quality(processed_text)
                if score > best_score:
                    best_score = score
                    best_text = processed_text
                    best_method = method
            
            processing_time = time.time() - start_time
            
            stats = {
                "method": best_method,
                "characters": len(best_text),
                "processing_time": processing_time,
                "quality_score": best_score,
                "arabic_chars": sum(1 for c in best_text if '\u0600' <= c <= '\u06FF'),
                "lines": len(best_text.splitlines()),
                "pages": page_count
            }
            
            logger.info(f"[Direct] Extracted {len(best_text)} characters using {best_method} method")
            return best_text, stats
            
        except Exception as e:
            logger.error(f"Direct extraction failed: {e}")
            return "", {"error": str(e)}
    
    def _preprocess_images(self, page_image):
        """Preprocess images for better Arabic OCR"""
        processed_images = {"original": page_image}
        
        try:
            # Basic PIL preprocessing techniques (always available)
            if ImageEnhance is not None:
                # Technique 1: Enhance contrast
                enhancer = ImageEnhance.Contrast(page_image)
                processed_images["contrast"] = enhancer.enhance(1.5)
                
                # Technique 2: Enhance sharpness
                enhancer = ImageEnhance.Sharpness(page_image)
                processed_images["sharp"] = enhancer.enhance(1.5)
                
                # Technique 3: Convert to grayscale and enhance
                gray = page_image.convert('L')
                enhancer = ImageEnhance.Contrast(gray)
                processed_images["gray_contrast"] = enhancer.enhance(1.3)
            
            # Advanced OpenCV preprocessing (if available)
            if OPENCV_AVAILABLE and cv2 is not None and np is not None:
                try:
                    # Convert PIL image to OpenCV format
                    cv_image = cv2.cvtColor(np.array(page_image), cv2.COLOR_RGB2BGR)
                    
                    # Technique 4: Binary threshold using OpenCV
                    gray_cv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                    _, binary = cv2.threshold(gray_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    binary_pil = Image.fromarray(binary)
                    processed_images["binary"] = binary_pil
                    
                    # Technique 5: Adaptive threshold
                    adaptive = cv2.adaptiveThreshold(gray_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                    adaptive_pil = Image.fromarray(adaptive)
                    processed_images["adaptive"] = adaptive_pil
                    
                except Exception as cv_e:
                    logger.warning(f"OpenCV preprocessing failed: {cv_e}")
                
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            # If preprocessing fails, just use original image
            processed_images = {"original": page_image}
        
        return processed_images
    
    def _clean_fragmented_text(self, text: str) -> str:
        """Clean fragmented and garbled Arabic text"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                cleaned_lines.append(line)
                continue
            
            # Check if line is heavily fragmented
            words = line.split()
            if len(words) == 0:
                continue
            
            # Count fragmented words (single characters or repeated patterns)
            fragmented_count = 0
            for word in words:
                # Check for single character words
                if len(word.strip()) <= 1:
                    fragmented_count += 1
                    continue
                
                # Check for repeated character patterns (like "ممه ممه ممه")
                if len(word) >= 3:
                    # Count unique characters vs total characters
                    unique_chars = len(set(word))
                    if unique_chars <= 2 and len(word) >= 3:  # Mostly repeated chars
                        fragmented_count += 1
                        continue
                    
                    # Check for excessive repetition of same character
                    char_counts = {}
                    for char in word:
                        char_counts[char] = char_counts.get(char, 0) + 1
                    max_repetition = max(char_counts.values())
                    if max_repetition >= len(word) * 0.6:  # 60% same character
                        fragmented_count += 1
                        continue
            
            # Skip line if more than 50% of words are fragmented
            fragmentation_ratio = fragmented_count / len(words) if words else 0
            if fragmentation_ratio <= 0.5:
                cleaned_lines.append(line)
            else:
                # Skip this fragmented line
                logger.debug(f"Skipping fragmented line: {line[:50]}...")
        
        return '\n'.join(cleaned_lines)
    
    def extract_ocr(self, pdf_path: str, dpi: int = 300) -> Tuple[str, Dict]:
        """Enhanced OCR extraction with configurable parameters"""
        if not self.ocr_available:
            logger.error("OCR libraries not available")
            return "", {"error": "OCR libraries not installed"}
        
        try:
            start_time = time.time()
            
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=dpi)
            logger.info(f"Converted {len(pages)} pages to images at {dpi} DPI")
            
            all_text = ""
            page_stats = []
            
            for i, page in enumerate(pages):
                page_start = time.time()
                
                # Try multiple image preprocessing techniques
                processed_images = self._preprocess_images(page)
                
                best_page_text = ""
                best_config = "default"
                best_confidence = 0
                
                # Try OCR configurations with different preprocessing
                ocr_configs = [
                    ("--oem 3 --psm 6 -c tessedit_char_whitelist=٠١٢٣٤٥٦٧٨٩ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?:()[]{}/-\\ ا-يءآأإؤئبتثجحخدذرزسشصضطظعغفقكلمنهوي", "arabic_optimized"),
                    ("--oem 3 --psm 3", "fully_automatic"),
                    ("--oem 1 --psm 6", "LSTM"),
                    ("--oem 3 --psm 1", "auto_page"),
                    ("--oem 3 --psm 11", "single_word"),
                ]
                
                best_page_text = ""
                best_config = "default"
                best_confidence = 0
                
                # Try each OCR config with each preprocessed image
                for config, config_name in ocr_configs:
                    for img_name, processed_img in processed_images.items():
                        try:
                            page_text = pytesseract.image_to_string(
                                processed_img, lang="ara", config=config
                            )
                            
                            # Enhanced confidence estimation
                            confidence = self._estimate_ocr_confidence(page_text)
                            
                            if confidence > best_confidence:
                                best_confidence = confidence
                                best_page_text = page_text
                                best_config = f"{config_name}_{img_name}"
                                
                        except Exception as e:
                            logger.warning(f"OCR config {config_name}_{img_name} failed: {e}")
                            continue
                
                # Clean fragmented text before adding to results
                cleaned_page_text = self._clean_fragmented_text(best_page_text)
                
                # OCR text is already properly formatted, don't apply Arabic processing
                # This prevents double-processing that causes character reversal
                logger.info(f"OCR output: {len(cleaned_page_text)} characters extracted (cleaned from {len(best_page_text)})")
                
                all_text += cleaned_page_text + "\n"
                
                page_time = time.time() - page_start
                page_stats.append({
                    "page": i + 1,
                    "config": best_config,
                    "confidence": best_confidence,
                    "processing_time": page_time,
                    "characters": len(best_page_text)
                })
                
                logger.info(f"OCR processing page {i+1}/{len(pages)} using {best_config} config...")
            
            processing_time = time.time() - start_time
            
            stats = {
                "pages": len(pages),
                "dpi": dpi,
                "processing_time": processing_time,
                "characters": len(all_text),
                "arabic_chars": sum(1 for c in all_text if '\u0600' <= c <= '\u06FF'),
                "lines": len(all_text.splitlines()),
                "page_stats": page_stats,
                "avg_confidence": sum(p['confidence'] for p in page_stats) / len(page_stats) if page_stats else 0
            }
            
            logger.info(f"[OCR] Extracted {len(all_text)} characters")
            return all_text, stats
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return "", {"error": str(e)}
    
    def _assess_extraction_quality(self, text: str) -> float:
        """Assess the quality of extracted text"""
        if not text.strip():
            return 0.0
        
        score = 0.0
        
        # Length score (longer text is generally better)
        length_score = min(len(text) / 1000, 1.0)  # Max score at 1000 chars
        score += length_score * 0.3
        
        # Arabic content score
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if len(text) > 0:
            arabic_ratio = arabic_chars / len(text)
            score += arabic_ratio * 0.4
        
        # Structure score (reasonable line lengths)
        lines = text.split('\n')
        if lines:
            avg_line_length = sum(len(line.strip()) for line in lines if line.strip()) / len([l for l in lines if l.strip()])
            if avg_line_length > 10:
                score += 0.3
        
        return score
    
    def _estimate_ocr_confidence(self, text: str) -> float:
        """Estimate OCR confidence based on text characteristics"""
        if not text.strip():
            return 0.0
        
        confidence = 0.0
        
        # Check for Arabic character presence and quality
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if len(text) > 0:
            arabic_ratio = arabic_chars / len(text)
            
            # Strong Arabic content gets higher confidence
            if arabic_ratio > 0.5:
                confidence += 0.4
            elif arabic_ratio > 0.3:
                confidence += 0.3
            elif arabic_ratio > 0.1:
                confidence += 0.2
        
        # Check for reasonable word lengths (avoid fragmented text)
        words = text.split()
        if words:
            valid_words = [w for w in words if len(w.strip()) > 1]
            if len(valid_words) > 0:
                avg_word_length = sum(len(w) for w in valid_words) / len(valid_words)
                if 2 <= avg_word_length <= 12:  # Reasonable Arabic word length
                    confidence += 0.3
                elif avg_word_length < 1.5:  # Too fragmented
                    confidence -= 0.3
        
        # Check for excessive fragmentation (many single-character "words")
        single_char_words = sum(1 for w in words if len(w.strip()) == 1)
        if len(words) > 0 and single_char_words / len(words) > 0.5:
            confidence -= 0.4  # Heavily fragmented text
        
        # Check for repeated character patterns (like "ممه ممه ممه")
        repeated_pattern_words = 0
        for word in words:
            if len(word) >= 3:
                # Check for mostly repeated characters
                unique_chars = len(set(word))
                if unique_chars <= 2 and len(word) >= 3:
                    repeated_pattern_words += 1
                else:
                    # Check for excessive repetition of same character
                    char_counts = {}
                    for char in word:
                        char_counts[char] = char_counts.get(char, 0) + 1
                    max_repetition = max(char_counts.values())
                    if max_repetition >= len(word) * 0.6:  # 60% same character
                        repeated_pattern_words += 1
        
        if len(words) > 0 and repeated_pattern_words / len(words) > 0.3:
            confidence -= 0.3  # Too many repeated pattern words
        
        # Check for coherent Arabic patterns
        lines = text.split('\n')
        coherent_lines = 0
        for line in lines:
            if len(line.strip()) > 10:  # Reasonable line length
                coherent_lines += 1
        
        if len(lines) > 0:
            coherence_ratio = coherent_lines / len(lines)
            confidence += coherence_ratio * 0.3
        
        return max(0.0, min(confidence, 1.0))

def save_results(direct_text: str, ocr_text: str, direct_stats: Dict, ocr_stats: Dict, output_dir: str):
    """Save extraction results with comprehensive metadata"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save text files
    direct_file = output_path / "output_direct.txt"
    ocr_file = output_path / "output_ocr.txt"
    
    with open(direct_file, 'w', encoding='utf-8') as f:
        f.write(direct_text)
    
    with open(ocr_file, 'w', encoding='utf-8') as f:
        f.write(ocr_text)
    
    # Save comprehensive statistics
    stats = {
        "extraction_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "direct_extraction": direct_stats,
        "ocr_extraction": ocr_stats,
        "comparison": {
            "direct_characters": len(direct_text),
            "ocr_characters": len(ocr_text),
            "direct_arabic_chars": sum(1 for c in direct_text if '\u0600' <= c <= '\u06FF'),
            "ocr_arabic_chars": sum(1 for c in ocr_text if '\u0600' <= c <= '\u06FF'),
            "recommended_method": "direct" if len(direct_text) > len(ocr_text) else "ocr"
        }
    }
    
    stats_file = output_path / "extraction_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Direct: {len(direct_text)} chars, OCR: {len(ocr_text)} chars")

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Arabic PDF Text Extraction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_arabic_pdf_enhanced.py document.pdf
  python extract_arabic_pdf_enhanced.py document.pdf --output-dir ./results
  python extract_arabic_pdf_enhanced.py document.pdf --dpi 400 --ocr-only
        """
    )
    
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output-dir', default='.', help='Output directory (default: current directory)')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for OCR processing (default: 300)')
    parser.add_argument('--direct-only', action='store_true', help='Only use direct extraction')
    parser.add_argument('--ocr-only', action='store_true', help='Only use OCR extraction')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        sys.exit(1)
    
    if not pdf_path.suffix.lower() == '.pdf':
        logger.error(f"File is not a PDF: {pdf_path}")
        sys.exit(1)
    
    logger.info(f"Processing file: {pdf_path}")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Initialize processors
    arabic_processor = ArabicTextProcessor()
    extractor = PDFExtractor(arabic_processor)
    
    # Extraction
    direct_text = ""
    ocr_text = ""
    direct_stats = {}
    ocr_stats = {}
    
    if not args.ocr_only:
        logger.info("Starting direct text extraction...")
        direct_text, direct_stats = extractor.extract_direct(str(pdf_path))
    
    if not args.direct_only:
        logger.info("Starting OCR text extraction...")
        ocr_text, ocr_stats = extractor.extract_ocr(str(pdf_path), args.dpi)
    
    # Save results
    save_results(direct_text, ocr_text, direct_stats, ocr_stats, args.output_dir)
    
    # Summary
    logger.info("=" * 60)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 60)
    
    if direct_text and ocr_text:
        logger.info(f"Direct extraction: {len(direct_text)} characters")
        logger.info(f"OCR extraction: {len(ocr_text)} characters")
        
        if len(direct_text) > len(ocr_text):
            logger.info("RECOMMENDATION: Direct extraction yielded more text")
        else:
            logger.info("RECOMMENDATION: OCR extraction yielded more text")
    
    elif direct_text:
        logger.info(f"Direct extraction succeeded: {len(direct_text)} characters")
    
    elif ocr_text:
        logger.info(f"OCR extraction succeeded: {len(ocr_text)} characters")
    
    else:
        logger.error("Both extraction methods failed")
        sys.exit(1)
    
    logger.info("Extraction completed successfully!")

if __name__ == "__main__":
    main()
