import sys
import logging
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import arabic_reshaper
from bidi.algorithm import get_display

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def needs_fixing(text: str) -> bool:
    """Check if text needs Arabic fixing"""
    if not text.strip():
        return False
    
    # Check for artifacts (isolated Unicode characters)
    artifacts = ['ﻢ', 'ﻪ', 'ﻆ', 'ﺍ', 'ﺕ', 'ﺏ', 'ﻞ', 'ﺝ', 'ﺡ', 'ﺥ', 'ﺩ', 'ﺫ', 'ﺭ', 'ﺯ', 'ﺱ', 'ﺵ', 'ﺹ', 'ﺽ', 'ﻁ', 'ﻅ', 'ﻉ', 'ﻍ', 'ﻑ', 'ﻕ', 'ﻙ', 'ﻝ', 'ﻡ', 'ﻥ', 'ﻩ', 'ﻭ', 'ﻱ']
    if any(artifact in text for artifact in artifacts):
        return True
    
    # Check for fragmented words
    words = text.split()
    if words:
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len <= 2:
            return True
    
    # Check for Arabic characters
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    arabic_ratio = arabic_chars / len(text.strip()) if text.strip() else 0
    if arabic_ratio > 0.1:
        return True
    
    return False


def fix_arabic_text(text: str, reverse_words=False) -> str:
    """
    Apply reshape + bidi for Arabic text
    
    Args:
        text: Input text
        reverse_words: If True, reverse word order (for OCR text that's backward)
    """
    try:
        # If text is backward (OCR issue), reverse word order first
        if reverse_words:
            words = text.split()
            text = ' '.join(reversed(words))
        
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception as e:
        logging.warning(f"Failed to fix Arabic text: {e}")
        return text


def extract_text_direct(pdf_path: str) -> str:
    """Extract text directly from PDF using PyMuPDF dict method"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        logging.info(f"Direct extraction: Processing {len(doc)} pages...")
        
        for page_num, page in enumerate(doc, 1):
            # Use get_text("dict") for structured extraction
            page_dict = page.get_text("dict")
            
            if page_dict and "blocks" in page_dict:
                for block in page_dict["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            if "spans" in line:
                                line_text = ""
                                for span in line["spans"]:
                                    if "text" in span and span["text"].strip():
                                        line_text += span["text"]
                                
                                if line_text.strip():
                                    if needs_fixing(line_text):
                                        line_text = fix_arabic_text(line_text)
                                    text += line_text + "\n"
        
        doc.close()
        logging.info(f"[Direct] Extracted {len(text)} characters")
        return text
        
    except Exception as e:
        logging.error(f"Direct extraction failed: {e}")
        return ""


def extract_text_ocr(pdf_path: str) -> str:
    """Extract text using OCR with PyMuPDF for image conversion"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        logging.info(f"OCR extraction: Processing {len(doc)} pages...")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            logging.info(f"OCR processing page {page_num + 1}/{len(doc)}...")
            
            # Convert page to image using PyMuPDF
            # Higher resolution = better OCR quality
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom = 144 DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Convert pixmap to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Apply Tesseract OCR
            # --psm 4: Single column of text
            # --psm 6: Uniform block of text (default)
            # --oem 3: Default OCR Engine Mode
            page_text = pytesseract.image_to_string(
                img, 
                lang="ara",  # Arabic language
                config="--oem 3 --psm 4"
            )
            
            if page_text.strip():
                # Apply Arabic fixing - OCR text is often backward, so reverse words
                if needs_fixing(page_text):
                    page_text = fix_arabic_text(page_text, reverse_words=True)
                text += page_text + "\n\n"
                logging.info(f"Page {page_num + 1}: Extracted {len(page_text)} characters")
            else:
                logging.warning(f"Page {page_num + 1}: No text extracted")
        
        doc.close()
        logging.info(f"[OCR] Total extracted: {len(text)} characters")
        return text
        
    except Exception as e:
        logging.error(f"OCR extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return ""


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_with_ocr.py <file.pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    logging.info(f"Processing file: {pdf_path}")
    
    # 1. Direct Extraction
    logging.info("\n" + "="*60)
    logging.info("METHOD 1: Direct Text Extraction")
    logging.info("="*60)
    direct_text = extract_text_direct(pdf_path)
    with open("output_direct.txt", "w", encoding="utf-8") as f:
        f.write(direct_text)
    logging.info(f"Saved to: output_direct.txt ({len(direct_text)} chars)")
    
    # 2. OCR Extraction
    logging.info("\n" + "="*60)
    logging.info("METHOD 2: OCR Extraction (Tesseract)")
    logging.info("="*60)
    ocr_text = extract_text_ocr(pdf_path)
    with open("output_ocr.txt", "w", encoding="utf-8") as f:
        f.write(ocr_text)
    logging.info(f"Saved to: output_ocr.txt ({len(ocr_text)} chars)")
    
    # 3. Comparison
    logging.info("\n" + "="*60)
    logging.info("COMPARISON")
    logging.info("="*60)
    logging.info(f"Direct extraction: {len(direct_text)} characters")
    logging.info(f"OCR extraction: {len(ocr_text)} characters")
    
    if len(direct_text) > len(ocr_text) * 0.8:
        logging.info("✅ Recommendation: Use Direct extraction (more reliable)")
        recommended = direct_text
    else:
        logging.info("✅ Recommendation: Use OCR extraction (direct failed or incomplete)")
        recommended = ocr_text
    
    with open("output_best.txt", "w", encoding="utf-8") as f:
        f.write(recommended)
    logging.info(f"Saved best result to: output_best.txt")
    
    logging.info("\nExtraction finished!")


if __name__ == "__main__":
    main()

