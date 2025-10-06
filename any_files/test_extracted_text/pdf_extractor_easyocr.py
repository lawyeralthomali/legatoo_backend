#!/usr/bin/env python3
"""
Enhanced Arabic PDF Text Extraction Script with EasyOCR Support
==============================================================

A robust script for extracting Arabic text from PDF files with multiple OCR engines.
Supports Direct extraction, Tesseract OCR, and EasyOCR for better Arabic text handling.

Features:
- Triple extraction methods (Direct + Tesseract OCR + EasyOCR)
- Better Arabic text direction handling
- Quality assessment and comparison
- Comprehensive error handling
- Progress tracking and logging
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
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None
    convert_from_path = None
    Image = None
    ImageEnhance = None
    ImageFilter = None

# EasyOCR support
try:
    import easyocr as easyocr_lib
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    easyocr_lib = None

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
        """Detect if Arabic text needs processing"""
        if not text.strip():
            return False
        
        # Check for Arabic characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if arabic_chars == 0:
            return False
        
        # Simple detection: if average word length is very short, likely fragmented
        words = text.split()
        if len(words) == 0:
            return False
        
        avg_word_len = sum(len(w) for w in words) / len(words)
        return avg_word_len <= 2
    
    def fix_arabic_text(self, text: str) -> str:
        """Fix Arabic text using reshaping and bidirectional algorithm"""
        if not self.arabic_available or not text.strip():
            return text
        
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception as e:
            logger.error(f"Error in Arabic text processing: {e}")
            return text

class PDFExtractor:
    """Enhanced PDF text extractor with multiple OCR engines"""
    
    def __init__(self, arabic_processor: ArabicTextProcessor):
        self.arabic_processor = arabic_processor
        self.fitz_available = FITZ_AVAILABLE
        self.tesseract_available = TESSERACT_AVAILABLE
        self.easyocr_available = EASYOCR_AVAILABLE
        
        # Initialize EasyOCR reader if available
        self.easyocr_reader = None
        if self.easyocr_available:
            try:
                logger.info("Initializing EasyOCR with Arabic support...")
                self.easyocr_reader = easyocr_lib.Reader(['ar', 'en'], gpu=False)
                logger.info("EasyOCR initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR: {e}")
                self.easyocr_available = False
    
    def extract_direct(self, pdf_path: str) -> Tuple[str, Dict]:
        """Direct text extraction using PyMuPDF"""
        if not self.fitz_available:
            logger.error("PyMuPDF not available for direct extraction")
            return "", {"error": "PyMuPDF not installed"}
        
        try:
            start_time = time.time()
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            
            # Try different extraction methods
            methods_results = []
            
            # Method 1: Standard text extraction
            try:
                text_standard = ""
                for page in doc:
                    text_standard += page.get_text() + "\n"
                methods_results.append(("standard", text_standard))
            except Exception as e:
                logger.warning(f"Standard extraction failed: {e}")
                methods_results.append(("standard", ""))
            
            # Method 2: Blocks extraction
            try:
                text_blocks = ""
                for page in doc:
                    blocks = page.get_text("blocks")
                    if blocks:
                        text_blocks += "\n".join([block[4] for block in blocks if block[4].strip()]) + "\n"
                methods_results.append(("blocks", text_blocks))
            except Exception as e:
                logger.warning(f"Blocks extraction failed: {e}")
                methods_results.append(("blocks", ""))
            
            doc.close()
            
            # Choose the best method
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
    
    def extract_tesseract_ocr(self, pdf_path: str, dpi: int = 300) -> Tuple[str, Dict]:
        """OCR extraction using Tesseract"""
        if not self.tesseract_available:
            logger.error("Tesseract libraries not available")
            return "", {"error": "Tesseract libraries not installed"}
        
        try:
            start_time = time.time()
            pages = convert_from_path(pdf_path, dpi=dpi)
            logger.info(f"Converted {len(pages)} pages to images at {dpi} DPI")
            
            all_text = ""
            page_stats = []
            
            for i, page in enumerate(pages):
                page_start = time.time()
                
                # Try different OCR configurations
                ocr_configs = [
                    ("--oem 3 --psm 6", "arabic_optimized"),
                    ("--oem 3 --psm 3", "fully_automatic"),
                    ("--oem 1 --psm 6", "LSTM"),
                ]
                
                best_page_text = ""
                best_config = "default"
                best_confidence = 0
                
                for config, config_name in ocr_configs:
                    try:
                        page_text = pytesseract.image_to_string(
                            page, lang="ara", config=config
                        )
                        
                        confidence = self._estimate_ocr_confidence(page_text)
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_page_text = page_text
                            best_config = config_name
                            
                    except Exception as e:
                        logger.warning(f"Tesseract config {config_name} failed: {e}")
                        continue
                
                all_text += best_page_text + "\n"
                
                page_time = time.time() - page_start
                page_stats.append({
                    "page": i + 1,
                    "config": best_config,
                    "confidence": best_confidence,
                    "processing_time": page_time,
                    "characters": len(best_page_text)
                })
                
                logger.info(f"Tesseract processing page {i+1}/{len(pages)} using {best_config} config...")
            
            processing_time = time.time() - start_time
            
            stats = {
                "engine": "tesseract",
                "pages": len(pages),
                "dpi": dpi,
                "processing_time": processing_time,
                "characters": len(all_text),
                "arabic_chars": sum(1 for c in all_text if '\u0600' <= c <= '\u06FF'),
                "lines": len(all_text.splitlines()),
                "page_stats": page_stats,
                "avg_confidence": sum(p['confidence'] for p in page_stats) / len(page_stats) if page_stats else 0
            }
            
            logger.info(f"[Tesseract] Extracted {len(all_text)} characters")
            return all_text, stats
            
        except Exception as e:
            logger.error(f"Tesseract OCR extraction failed: {e}")
            return "", {"error": str(e)}
    
    def extract_easyocr(self, pdf_path: str, dpi: int = 300) -> Tuple[str, Dict]:
        """OCR extraction using EasyOCR - better for Arabic text direction"""
        if not self.easyocr_available or not self.easyocr_reader:
            logger.error("EasyOCR not available")
            return "", {"error": "EasyOCR not installed or initialized"}
        
        try:
            start_time = time.time()
            pages = convert_from_path(pdf_path, dpi=dpi)
            logger.info(f"Converted {len(pages)} pages to images at {dpi} DPI for EasyOCR")
            
            all_text = ""
            page_stats = []
            
            for i, page in enumerate(pages):
                page_start = time.time()
                
                try:
                    # Convert PIL image to numpy array for EasyOCR
                    page_array = np.array(page)
                    
                    # Extract text using EasyOCR
                    results = self.easyocr_reader.readtext(page_array)
                    
                    # Process results - EasyOCR handles Arabic direction better
                    page_text = ""
                    total_confidence = 0
                    valid_results = 0
                    
                    for (bbox, text, confidence) in results:
                        if confidence > 0.1:  # Filter low confidence results
                            page_text += text + " "
                            total_confidence += confidence
                            valid_results += 1
                    
                    avg_confidence = total_confidence / valid_results if valid_results > 0 else 0
                    
                    all_text += page_text + "\n"
                    
                    page_time = time.time() - page_start
                    page_stats.append({
                        "page": i + 1,
                        "confidence": avg_confidence,
                        "processing_time": page_time,
                        "characters": len(page_text),
                        "valid_results": valid_results
                    })
                    
                    logger.info(f"EasyOCR processing page {i+1}/{len(pages)} - confidence: {avg_confidence:.2f}")
                    
                except Exception as e:
                    logger.warning(f"EasyOCR failed on page {i+1}: {e}")
                    page_stats.append({
                        "page": i + 1,
                        "confidence": 0,
                        "processing_time": 0,
                        "characters": 0,
                        "error": str(e)
                    })
            
            processing_time = time.time() - start_time
            
            stats = {
                "engine": "easyocr",
                "pages": len(pages),
                "dpi": dpi,
                "processing_time": processing_time,
                "characters": len(all_text),
                "arabic_chars": sum(1 for c in all_text if '\u0600' <= c <= '\u06FF'),
                "lines": len(all_text.splitlines()),
                "page_stats": page_stats,
                "avg_confidence": sum(p['confidence'] for p in page_stats) / len(page_stats) if page_stats else 0
            }
            
            logger.info(f"[EasyOCR] Extracted {len(all_text)} characters")
            return all_text, stats
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return "", {"error": str(e)}
    
    def _assess_extraction_quality(self, text: str) -> float:
        """Assess the quality of extracted text"""
        if not text.strip():
            return 0.0
        
        score = 0.0
        
        # Length score
        length_score = min(len(text) / 1000, 1.0)
        score += length_score * 0.3
        
        # Arabic content score
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if len(text) > 0:
            arabic_ratio = arabic_chars / len(text)
            score += arabic_ratio * 0.4
        
        # Structure score
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
        
        # Check for Arabic character presence
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if len(text) > 0:
            arabic_ratio = arabic_chars / len(text)
            if arabic_ratio > 0.5:
                confidence += 0.4
            elif arabic_ratio > 0.3:
                confidence += 0.3
        
        # Check for reasonable word lengths
        words = text.split()
        if words:
            valid_words = [w for w in words if len(w.strip()) > 1]
            if len(valid_words) > 0:
                avg_word_length = sum(len(w) for w in valid_words) / len(valid_words)
                if 2 <= avg_word_length <= 12:
                    confidence += 0.3
        
        return max(0.0, min(confidence, 1.0))

def save_results(results: Dict[str, Tuple[str, Dict]], output_dir: str):
    """Save extraction results from all methods"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save text files for each method
    for method, (text, stats) in results.items():
        if text:  # Only save if we have text
            output_file = output_path / f"output_{method}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Saved {method} results to {output_file}")
    
    # Save comprehensive statistics
    extraction_stats = {
        "extraction_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "methods": {}
    }
    
    for method, (text, stats) in results.items():
        extraction_stats["methods"][method] = {
            "characters": len(text),
            "arabic_chars": sum(1 for c in text if '\u0600' <= c <= '\u06FF'),
            "lines": len(text.splitlines()),
            "stats": stats
        }
    
    # Determine best method
    best_method = "direct"
    best_score = 0
    for method, (text, stats) in results.items():
        if text and len(text) > best_score:
            best_score = len(text)
            best_method = method
    
    extraction_stats["recommended_method"] = best_method
    extraction_stats["comparison"] = {
        "methods_tried": list(results.keys()),
        "successful_extractions": [method for method, (text, _) in results.items() if text]
    }
    
    stats_file = output_path / "extraction_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(extraction_stats, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Arabic PDF Text Extraction Tool with EasyOCR Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 esayocr.py document.pdf
  python3 esayocr.py document.pdf --output-dir ./results
  python3 esayocr.py document.pdf --dpi 400 --easyocr-only
        """
    )
    
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output-dir', default='./out', help='Output directory (default: ./out)')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for OCR processing (default: 300)')
    parser.add_argument('--direct-only', action='store_true', help='Only use direct extraction')
    parser.add_argument('--tesseract-only', action='store_true', help='Only use Tesseract OCR')
    parser.add_argument('--easyocr-only', action='store_true', help='Only use EasyOCR')
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
    
    # Check available methods
    logger.info("Available extraction methods:")
    logger.info(f"  - Direct extraction: {'✓' if FITZ_AVAILABLE else '✗'}")
    logger.info(f"  - Tesseract OCR: {'✓' if TESSERACT_AVAILABLE else '✗'}")
    logger.info(f"  - EasyOCR: {'✓' if EASYOCR_AVAILABLE else '✗'}")
    
    # Initialize processors
    arabic_processor = ArabicTextProcessor()
    extractor = PDFExtractor(arabic_processor)
    
    # Extraction
    results = {}
    
    if not args.tesseract_only and not args.easyocr_only:
        logger.info("Starting direct text extraction...")
        direct_text, direct_stats = extractor.extract_direct(str(pdf_path))
        if direct_text:
            results["direct"] = (direct_text, direct_stats)
    
    if not args.direct_only and not args.easyocr_only:
        logger.info("Starting Tesseract OCR extraction...")
        tesseract_text, tesseract_stats = extractor.extract_tesseract_ocr(str(pdf_path), args.dpi)
        if tesseract_text:
            results["tesseract"] = (tesseract_text, tesseract_stats)
    
    if not args.direct_only and not args.tesseract_only:
        logger.info("Starting EasyOCR extraction...")
        easyocr_text, easyocr_stats = extractor.extract_easyocr(str(pdf_path), args.dpi)
        if easyocr_text:
            results["easyocr"] = (easyocr_text, easyocr_stats)
    
    # Save results
    if results:
        save_results(results, args.output_dir)
    else:
        logger.error("All extraction methods failed")
        sys.exit(1)
    
    # Summary
    logger.info("=" * 60)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 60)
    
    for method, (text, stats) in results.items():
        logger.info(f"{method.upper()} extraction: {len(text)} characters")
        if 'arabic_chars' in stats:
            logger.info(f"  - Arabic characters: {stats['arabic_chars']}")
        if 'avg_confidence' in stats:
            logger.info(f"  - Average confidence: {stats['avg_confidence']:.2f}")
    
    # Recommend best method
    best_method = max(results.keys(), key=lambda k: len(results[k][0]))
    logger.info(f"\nRECOMMENDATION: {best_method.upper()} extraction yielded the most text")
    
    logger.info("Extraction completed successfully!")

if __name__ == "__main__":
    main()
