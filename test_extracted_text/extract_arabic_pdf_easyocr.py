import sys
import logging
import fitz  # PyMuPDF
import easyocr
from pdf2image import convert_from_path
from PIL import Image
import arabic_reshaper
from bidi.algorithm import get_display
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# EasyOCR reader will be initialized when needed

# ---------- [ أدوات إصلاح النصوص العربية ] ----------
def needs_fixing(text: str) -> bool:
    """
    Enhanced detection of Arabic text that needs fixing - ALWAYS fix Arabic text in PDFs
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


def fix_arabic_text(text: str) -> str:
    """Comprehensive Arabic text fixing with proper RTL handling"""
    if not text.strip():
        return text
    
    # Step 1: Clean Unicode artifacts first
    cleaned_text = clean_text_artifacts(text)
    
    # Step 2: Normalize fragmented text - merge broken letters into words
    normalized = normalize_fragmented_arabic(cleaned_text)
    
    # Step 3: Apply reshaping to Arabic words only (don't apply BiDi yet)
    words = normalized.split()
    reshaped_words = []
    
    for word in words:
        # Check if word contains Arabic characters
        arabic_chars = sum(1 for c in word if '\u0600' <= c <= '\u06FF')
        if arabic_chars > 0:
            # Apply reshaping to Arabic words
            reshaped_word = arabic_reshaper.reshape(word)
            reshaped_words.append(reshaped_word)
        else:
            # Keep non-Arabic words as-is
            reshaped_words.append(word)
    
    # Step 4: Join words (no BiDi processing here - will be done later)
    reshaped_text = ' '.join(reshaped_words)
    
    # Return the reshaped text without BiDi processing
    # BiDi will be applied in ensure_rtl_text_direction
    return reshaped_text


def normalize_fragmented_arabic(text: str) -> str:
    """Normalize fragmented Arabic text by merging isolated characters into words"""
    if not text.strip():
        return text
    
    # First clean artifacts
    cleaned_text = clean_text_artifacts(text)
    
    words = cleaned_text.split()
    normalized_words = []
    current_word = ""
    
    for word in words:
        word_clean = word.strip()
        if not word_clean:
            continue
            
        # If it's a single Arabic character, try to merge with previous Arabic content
        if len(word_clean) == 1 and '\u0600' <= word_clean <= '\u06FF':
            # Check if previous word was Arabic
            if current_word and any('\u0600' <= c <= '\u06FF' for c in current_word):
                current_word += word_clean
            else:
                # Start new Arabic word
                current_word = word_clean
        elif word_clean.isdigit() or word_clean.isalpha() or word_clean in ['.', ',', ':', ';']:
            # Non-Arabic word - finalize current Arabic word if exists
            if current_word:
                normalized_words.append(current_word)
                current_word = ""
            normalized_words.append(word_clean)
        else:
            # Mixed or other content
            arabic_chars = sum(1 for c in word_clean if '\u0600' <= c <= '\u06FF')
            if arabic_chars > len(word_clean) * 0.7:  # Mostly Arabic word
                if current_word:
                    current_word += word_clean
                else:
                    current_word = word_clean
            else:
                # Finalize current word and add this word
                if current_word:
                    normalized_words.append(current_word)
                    current_word = ""
                normalized_words.append(word_clean)
    
    # Add final word if exists
    if current_word:
        normalized_words.append(current_word)
    
    normalized_text = ' '.join(normalized_words)
    
    # Final cleanup
    normalized_text = clean_text_artifacts(normalized_text)
    
    return normalized_text


def clean_text_artifacts(text: str) -> str:
    """Remove artifacts and clean up text formatting"""
    if not text.strip():
        return text
    
    # Comprehensive Arabic Unicode artifact cleaning
    artifacts_map = {
        # Isolated forms
        'ﺍ': 'ا', 'ﺏ': 'ب', 'ﺕ': 'ت', 'ﺙ': 'ث', 'ﺝ': 'ج', 'ﺡ': 'ح', 'ﺥ': 'خ',
        'ﺩ': 'د', 'ﺫ': 'ذ', 'ﺭ': 'ر', 'ﺯ': 'ز', 'ﺱ': 'س', 'ﺵ': 'ش', 'ﺹ': 'ص',
        'ﺽ': 'ض', 'ﻁ': 'ط', 'ﻅ': 'ظ', 'ﻉ': 'ع', 'ﻍ': 'غ', 'ﻑ': 'ف', 'ﻕ': 'ق',
        'ﻙ': 'ك', 'ﻝ': 'ل', 'ﻡ': 'م', 'ﻥ': 'ن', 'ﻩ': 'ه', 'ﻭ': 'و', 'ﻱ': 'ي',
        
        # Initial forms
        'ﺑ': 'ب', 'ﺗ': 'ت', 'ﺛ': 'ث', 'ﺟ': 'ج', 'ﺣ': 'ح', 'ﺧ': 'خ', 'ﺳ': 'س',
        'ﺷ': 'ش', 'ﺻ': 'ص', 'ﺿ': 'ض', 'ﻃ': 'ط', 'ﻇ': 'ظ', 'ﻋ': 'ع', 'ﻏ': 'غ',
        'ﻓ': 'ف', 'ﻗ': 'ق', 'ﻛ': 'ك', 'ﻟ': 'ل', 'ﻣ': 'م', 'ﻧ': 'ن', 'ﻫ': 'ه', 'ﻳ': 'ي',
        
        # Medial forms
        'ﺒ': 'ب', 'ﺘ': 'ت', 'ﺜ': 'ث', 'ﺠ': 'ج', 'ﺤ': 'ح', 'ﺨ': 'خ', 'ﺴ': 'س',
        'ﺸ': 'ش', 'ﺼ': 'ص', 'ﻀ': 'ض', 'ﻄ': 'ط', 'ﻈ': 'ظ', 'ﻌ': 'ع', 'ﻐ': 'غ',
        'ﻔ': 'ف', 'ﻘ': 'ق', 'ﻜ': 'ك', 'ﻠ': 'ل', 'ﻤ': 'م', 'ﻨ': 'ن', 'ﻬ': 'ه', 'ﻴ': 'ي',
        
        # Final forms
        'ﺎ': 'ا', 'ﺐ': 'ب', 'ﺖ': 'ت', 'ﺚ': 'ث', 'ﺞ': 'ج', 'ﺢ': 'ح', 'ﺦ': 'خ',
        'ﺪ': 'د', 'ﺬ': 'ذ', 'ﺮ': 'ر', 'ﺰ': 'ز', 'ﺲ': 'س', 'ﺶ': 'ش', 'ﺺ': 'ص',
        'ﺾ': 'ض', 'ﻂ': 'ط', 'ﻆ': 'ظ', 'ﻊ': 'ع', 'ﻎ': 'غ', 'ﻒ': 'ف', 'ﻖ': 'ق',
        'ﻚ': 'ك', 'ﻞ': 'ل', 'ﻢ': 'م', 'ﻦ': 'ن', 'ﻪ': 'ه', 'ﻮ': 'و', 'ﻲ': 'ي'
    }
    
    # Apply mapping
    for artifact, replacement in artifacts_map.items():
        text = text.replace(artifact, replacement)
    
    # Remove any remaining isolated Unicode forms using regex
    import re
    # Pattern to match isolated Unicode presentation forms
    isolated_pattern = r'[\uFE70-\uFEFF]'
    text = re.sub(isolated_pattern, '', text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def ensure_rtl_text_direction(text: str) -> str:
    """Ensure Arabic text is displayed in proper RTL direction"""
    if not text.strip():
        return text
    
    # Check if text contains Arabic characters
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    if arabic_chars == 0:
        return text
    
    # Calculate Arabic ratio
    arabic_ratio = arabic_chars / len(text.strip()) if text.strip() else 0
    
    # Apply BiDi algorithm first
    try:
        if arabic_ratio > 0.3:  # More than 30% Arabic
            # Apply BiDi algorithm with Arabic base direction
            bidi_text = get_display(text)
            
            # Then add RTL marks for extra support
            rtl_wrapped = '\u200F' + bidi_text + '\u200F'
        else:
            # Mixed content - use default BiDi
            bidi_text = get_display(text)
            rtl_wrapped = bidi_text
            
    except Exception as e:
        logging.warning(f"BiDi processing error: {e}")
        # Fallback: use RTL override marks
        rtl_wrapped = '\u202E' + text + '\u202C'
        rtl_wrapped = '\u200F' + rtl_wrapped + '\u200F'
    
    return rtl_wrapped


# ---------- [ استخراج النص المباشر ] ----------
def extract_text_direct(pdf_path: str) -> str:
    """
    Extract text directly from PDF using PyMuPDF with deep iteration
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                logging.info(f"Processing page {page_num + 1} with dict extraction...")
                
                # Use get_text("dict") for deep iteration
                page_dict = page.get_text("dict")
                
                logging.info(f"Page {page_num + 1}: Found {len(page_dict.get('blocks', []))} blocks in dict")
                
                # Iterate through blocks -> lines -> spans
                for block_num, block in enumerate(page_dict.get('blocks', [])):
                    if 'lines' not in block:
                        continue
                    
                    for line_num, line in enumerate(block['lines']):
                        line_text = ""
                        
                        # Extract text from all spans in the line
                        for span_num, span in enumerate(line.get('spans', [])):
                            if 'text' in span:
                                span_text = span['text'].strip()
                                if span_text:
                                    line_text += span_text
                                else:
                                    logging.warning(f"Empty span {span_num} in line {line_num}, block {block_num}, page {page_num + 1}")
                            else:
                                logging.warning(f"Empty span {span_num} in line {line_num}, block {block_num}, page {page_num + 1}")
                        
                        # Apply Arabic fixing to the complete line
                        if line_text.strip():
                            # Always apply Arabic fixing and RTL direction for any Arabic content
                            if needs_fixing(line_text):
                                fixed_line = fix_arabic_text(line_text)
                                # Apply RTL direction for Arabic text
                                fixed_line = ensure_rtl_text_direction(fixed_line)
                                logging.debug(f"Fixed Arabic line: '{line_text[:30]}...' -> '{fixed_line[:30]}...'")
                            else:
                                # Check if line contains Arabic and needs RTL direction
                                fixed_line = ensure_rtl_text_direction(line_text)
                            text += fixed_line + "\n"
                        else:
                            logging.warning(f"Empty line {line_num} in block {block_num} at page {page_num + 1}")
                            text += "\n"  # نحتفظ بالسطر الفارغ للحفاظ على البنية
                
                # إضافة فصل بين الصفحات
                text += "\n---PAGE_SEPARATOR---\n"
                
            except Exception as page_e:
                logging.error(f"Error processing page {page_num + 1}: {page_e}")
                text += f"\n---ERROR_PAGE_{page_num + 1}---\n"
                continue
        
        doc.close()
        logging.info(f"[Direct] Extracted {len(text)} characters from {len(doc)} pages using dict extraction")
        return text
        
    except Exception as e:
        logging.error(f"Direct extraction failed: {e}")
        return ""


# ---------- [ استخراج النص بالـ EasyOCR ] ----------
def extract_text_easyocr(pdf_path: str) -> str:
    """
    Extract text using EasyOCR - more reliable for Arabic text
    """
    try:
        # Initialize EasyOCR reader here to avoid encoding issues during import
        logging.info("Initializing EasyOCR reader...")
        reader = easyocr.Reader(['ar', 'en'], gpu=False, verbose=False)
        
        pages = convert_from_path(pdf_path, dpi=300)
        text = ""
        
        for page_num, page in enumerate(pages, 1):
            try:
                logging.info(f"EasyOCR processing page {page_num}/{len(pages)}...")
                
                # Convert PIL image to numpy array for EasyOCR
                import numpy as np
                page_array = np.array(page)
                
                # Use EasyOCR to extract text
                results = reader.readtext(page_array, paragraph=False)
                
                if not results:
                    logging.warning(f"No EasyOCR text extracted from page {page_num}")
                    text += f"\n---NO_EASYOCR_PAGE_{page_num}---\n"
                    text += "\n---PAGE_SEPARATOR---\n"
                    continue
                
                logging.info(f"Page {page_num} EasyOCR: Found {len(results)} text blocks")
                
                # Process each detected text block
                for block_num, (bbox, detected_text, confidence) in enumerate(results):
                    if not detected_text.strip():
                        logging.warning(f"Empty EasyOCR block {block_num} at page {page_num}")
                        text += "\n"
                        continue
                    
                    # Print debug for detected content
                    logging.debug(f"Page {page_num}, Block {block_num}: '{detected_text[:50]}...' (confidence: {confidence:.2f})")
                    
                    # Apply Arabic fixing to each detected text block
                    if needs_fixing(detected_text):
                        fixed_text = fix_arabic_text(detected_text)
                        # Apply RTL direction for Arabic text
                        fixed_text = ensure_rtl_text_direction(fixed_text)
                        logging.debug(f"Fixed EasyOCR text: '{detected_text[:30]}...' -> '{fixed_text[:30]}...'")
                    else:
                        # Check if text contains Arabic and needs RTL direction
                        fixed_text = ensure_rtl_text_direction(detected_text)
                    
                    text += fixed_text + "\n"
                
                # إضافة فصل بين الصفحات
                text += "\n---PAGE_SEPARATOR---\n"
                
            except Exception as page_e:
                logging.error(f"Error processing EasyOCR page {page_num}: {page_e}")
                # حتى لو فشلت الصفحة، نحاول المتابعة
                text += f"\n---ERROR_PAGE_{page_num}---\n"
                text += "\n---PAGE_SEPARATOR---\n"
                continue
        
        logging.info(f"[EasyOCR] Extracted {len(text)} characters from {len(pages)} pages")
        return text
        
    except Exception as e:
        logging.error(f"EasyOCR extraction failed: {e}")
        return ""


# ---------- [ main ] ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_arabic_pdf_easyocr.py <file.pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found")
        sys.exit(1)
    
    print(f"Processing file: {pdf_path}")
    
    # استخراج النص المباشر
    logging.info("=== Starting Direct Text Extraction ===")
    direct_text = extract_text_direct(pdf_path)
    
    # استخراج النص بـ EasyOCR
    logging.info("=== Starting EasyOCR Text Extraction ===")
    easyocr_text = extract_text_easyocr(pdf_path)
    
    # حفظ النتائج
    with open("output_direct.txt", "w", encoding="utf-8") as f:
        f.write(direct_text)
    
    with open("output_easyocr.txt", "w", encoding="utf-8") as f:
        f.write(easyocr_text)
    
    # تحديد أفضل طريقة بناءً على كمية المحتوى العربي
    direct_arabic_count = sum(1 for c in direct_text if '\u0600' <= c <= '\u06FF')
    easyocr_arabic_count = sum(1 for c in easyocr_text if '\u0600' <= c <= '\u06FF')
    
    if easyocr_arabic_count > direct_arabic_count:
        best_text = easyocr_text
        best_method = "EasyOCR"
        logging.info(f"EasyOCR extraction yielded more Arabic content ({easyocr_arabic_count} vs {direct_arabic_count} chars)")
    else:
        best_text = direct_text
        best_method = "Direct"
        logging.info(f"Direct extraction yielded more Arabic content ({direct_arabic_count} vs {easyocr_arabic_count} chars)")
    
    with open("output_best.txt", "w", encoding="utf-8") as f:
        f.write(best_text)
    
    # حفظ إحصائيات
    with open("output_chars_count.txt", "w", encoding="utf-8") as f:
        f.write(f"Direct: {len(direct_text)} chars ({direct_arabic_count} Arabic)\n")
        f.write(f"EasyOCR: {len(easyocr_text)} chars ({easyocr_arabic_count} Arabic)\n")
        f.write(f"Best method: {best_method}\n")
    
    logging.info("Extraction finished!")
    logging.info(f"Direct: {len(direct_text)} chars ({direct_arabic_count} Arabic)")
    logging.info(f"EasyOCR: {len(easyocr_text)} chars ({easyocr_arabic_count} Arabic)")
    logging.info(f"Best method: {best_method}")
    logging.info("Results saved to output_direct.txt, output_easyocr.txt, and output_best.txt")


if __name__ == "__main__":
    main()
