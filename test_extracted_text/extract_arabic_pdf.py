import sys
import logging
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import arabic_reshaper
from bidi.algorithm import get_display

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
        # For better RTL handling, wrap Arabic text with RTL marks
        if hasattr(get_display, '__code__'):
            # Check if Arabic content dominates the text
            arabic_ratio = sum(1 for c in text_for_bidi if '\u0600' <= c <= '\u06FF') / len(text_for_bidi.strip()) if text_for_bidi.strip() else 0
            
            if arabic_ratio > 0.5:  # More than 50% Arabic
                # Prepend RTL mark for proper Arabic text direction
                rtl_text = '\u202F' + text_for_bidi + '\u202F'  # Use Narrow No-Black Space
                fixed_text = get_display(rtl_text)
            else:
                # Mixed content - use default BiDi processing
                fixed_text = get_display(text_for_bidi)
        else:
            # Direct BiDi processing
            fixed_text = get_display(text_for_bidi)
            
    except Exception as e:
        logging.warning(f"RTL processing error: {e}")
        # Fallback: just apply reshaping without BiDi
        fixed_text = text_for_bidi
    
    return fixed_text

def ensure_rtl_text_direction(text: str) -> str:
    """Ensure Arabic text is displayed in proper RTL direction"""
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

def normalize_fragmented_arabic(text: str) -> str:
    """Merge fragmented Arabic letters back into words"""
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
    normalized_text = clean_text_artifacts(normalized_text)
    
    return normalized_text

def _is_fragmented_arabic(word: str) -> bool:
    """Detect if word is fragmented Arabic"""
    # Check if word is mostly single Arabic characters or has artifacts
    arabic_chars = sum(1 for c in word if '\u0600' <= c <= '\u06FF')
    total_chars = len(word.strip())
    
    if total_chars == 0:
        return False
    
    # If word has Arabic characters and is very short, likely fragmented
    if arabic_chars > 0 and total_chars <= 2:
        return True
    
    # Check for common artifacts that break Arabic words
    artifacts = ['ﻢ', 'ﻪ', 'ﻆ', 'ﺍ', 'ﺕ', 'ﺏ', 'ﻞ', 'ﺝ', 'ﺡ', 'ﺥ', 'ﺩ', 'ﺫ', 'ﺭ', 'ﺯ', 'ﺱ', 'ﺵ', 'ﺹ', 'ﺽ', 'ﻁ', 'ﻅ', 'ﻉ', 'ﻍ', 'ﻑ', 'ﻕ', 'ﻙ', 'ﻝ', 'ﻡ', 'ﻥ', 'ﻩ', 'ﻭ', 'ﻱ']
    
    # If word contains mostly isolated Arabic characters, it's likely fragmented
    isolated_chars = sum(1 for c in word if c in artifacts)
    if isolated_chars >= len(word.strip()) * 0.5:
        return True
    
    return False

def clean_text_artifacts(text: str) -> str:
    """Remove artifacts and clean up text formatting"""
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
    import re
    
    # Remove any remaining isolated Unicode forms (Unicode range U+FE70-U+FEFC)
    text = re.sub(r'[\uFE70-\uFEFC]', lambda m: artifacts_map.get(m.group(), m.group()), text)
    
    return text


# ---------- [ استخراج النص مباشرة من PDF ] ----------
def extract_text_direct(pdf_path: str) -> str:
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num, page in enumerate(doc, 1):
            try:
                logging.info(f"Processing page {page_num} with dict extraction...")
                
                # استخدام get_text("dict") للحصول على كل النص الممكن
                page_dict = page.get_text("dict")
                
                if not page_dict or "blocks" not in page_dict:
                    logging.warning(f"No dict blocks found at page {page_num}")
                    text += f"\n---EMPTY_PAGE_{page_num}---\n"
                    continue
                
                blocks = page_dict["blocks"]
                logging.info(f"Page {page_num}: Found {len(blocks)} blocks in dict")
                
                # معالجة كل block منفرداً - عمق كامل: blocks -> lines -> spans
                for block_num, block in enumerate(blocks):
                    if "lines" not in block:
                        logging.warning(f"Block {block_num} at page {page_num} has no lines")
                        text += "\n"  # نحتفظ بالفاصل
                        continue
                    
                    lines = block["lines"]
                    logging.debug(f"Page {page_num}, Block {block_num}: Found {len(lines)} lines")
                    
                    # معالجة كل line منفرداً
                    for line_num, line in enumerate(lines):
                        if "spans" not in line:
                            logging.warning(f"Line {line_num} in block {block_num} at page {page_num} has no spans")
                            text += "\n"  # نحتفظ بالسطر الفارغ
                            continue
                        
                        spans = line["spans"]
                        line_text = ""
                        
                        # استخراج كل span منفرداً
                        for span_num, span in enumerate(spans):
                            if "text" not in span:
                                logging.warning(f"Span {span_num} in line {line_num}, block {block_num}, page {page_num} has no text")
                                continue
                            
                            span_text = span["text"]
                            if not span_text.strip():
                                logging.warning(f"Empty span {span_num} in line {line_num}, block {block_num}, page {page_num}")
                                line_text += " "  # نحتفظ بالمسافة
                                continue
                            
                            logging.debug(f"Page {page_num}, Block {block_num}, Line {line_num}, Span {span_num}: '{span_text[:30]}...'")
                            line_text += span_text
                        
                        # تطبيق fix_arabic_text على كل سطر (دائماً) - لا نتجاهل أي نص
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
                            logging.warning(f"Empty line {line_num} in block {block_num} at page {page_num}")
                            text += "\n"  # نحتفظ بالسطر الفارغ للحفاظ على البنية
                
                # إضافة فصل بين الصفحات
                text += "\n---PAGE_SEPARATOR---\n"
                
            except Exception as page_e:
                logging.error(f"Error processing page {page_num}: {page_e}")
                text += f"\n---ERROR_PAGE_{page_num}---\n"
                continue
        
        doc.close()
        logging.info(f"[Direct] Extracted {len(text)} characters from {len(doc)} pages using dict extraction")
        return text
        
    except Exception as e:
        logging.error(f"Direct extraction failed: {e}")
        return ""


# ---------- [ استخراج النص بالـ OCR ] ----------
def extract_text_ocr(pdf_path: str) -> str:
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        text = ""
        
        for page_num, page in enumerate(pages, 1):
            try:
                logging.info(f"OCR processing page {page_num}/{len(pages)}...")
                
                # استخدام --psm 4 كافتراضي (single column) بدلاً من --psm 6
                raw_page_text = pytesseract.image_to_string(
                    page, lang="ara", config="--oem 3 --psm 4"
                )
                
                # إذا لم يتم استخراج نص، نجرب --psm 11 (sparse text)
                if not raw_page_text.strip():
                    logging.warning(f"No text with --psm 4 from page {page_num}, trying --psm 11...")
                    raw_page_text = pytesseract.image_to_string(
                        page, lang="ara", config="--oem 3 --psm 11"
                    )
                
                if not raw_page_text.strip():
                    logging.warning(f"No OCR text extracted from page {page_num} with any PSM")
                    text += f"\n---NO_OCR_PAGE_{page_num}---\n"
                    text += "\n---PAGE_SEPARATOR---\n"
                    continue
                
                logging.info(f"Page {page_num} raw OCR: {len(raw_page_text)} characters")
                
                # تقسيم النص إلى أسطر - نحتفظ بكل سطر
                ocr_lines = raw_page_text.splitlines()
                logging.info(f"Page {page_num}: Found {len(ocr_lines)} lines from OCR")
                
                # معالجة كل سطر منفرداً - لا نتجاهل أي شيء
                for line_num, line in enumerate(ocr_lines):
                    if not line.strip():
                        logging.warning(f"Empty OCR line {line_num} at page {page_num}")
                        text += "\n"  # نحتفظ بالسطر الفارغ
                        continue
                    
                    # طباعة debug للمحتوى الخام
                    logging.debug(f"Page {page_num}, Line {line_num}: '{line[:50]}...'")
                    
                    # تطبيق fix_arabic_text على كل سطر - OCR دائماً يحتاج إصلاح للنصوص العربية
                    if needs_fixing(line):
                        fixed_line = fix_arabic_text(line)
                        # Apply RTL direction for OCR Arabic text
                        fixed_line = ensure_rtl_text_direction(fixed_line)
                        logging.debug(f"Fixed OCR line: '{line[:30]}...' -> '{fixed_line[:30]}...'")
                    else:
                        # Check if OCR line contains Arabic and needs RTL direction
                        fixed_line = ensure_rtl_text_direction(line)
                    text += fixed_line + "\n"
                
                # إضافة فصل بين الصفحات
                text += "\n---PAGE_SEPARATOR---\n"
                
            except Exception as page_e:
                logging.error(f"Error processing OCR page {page_num}: {page_e}")
                # حتى لو فشلت الصفحة، نحاول المتابعة
                text += f"\n---ERROR_PAGE_{page_num}---\n"
                text += "\n---PAGE_SEPARATOR---\n"
                continue
        
        logging.info(f"[OCR] Extracted {len(text)} characters from {len(pages)} pages using improved PSM")
        return text
        
    except Exception as e:
        logging.error(f"OCR extraction failed: {e}")
        return ""


# ---------- [ main ] ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_arabic_pdf.py <file.pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    logging.info(f"Processing file: {pdf_path}")

    # 1. Try Direct Extraction first
    logging.info("=== Starting Direct Text Extraction ===")
    direct_text = extract_text_direct(pdf_path)
    
    # Count characters and Arabic content for assessment
    direct_chars = len(direct_text)
    direct_arabic_chars = sum(1 for c in direct_text if '\u0600' <= c <= '\u06FF')
    
    # 2. Try OCR Extraction as backup/complement
    logging.info("=== Starting OCR Text Extraction ===")
    ocr_text = extract_text_ocr(pdf_path)
    
    # Count characters and Arabic content for assessment
    ocr_chars = len(ocr_text)
    ocr_arabic_chars = sum(1 for c in ocr_text if '\u0600' <= c <= '\u06FF')
    
    # Choose the best result (more Arabic content is better for legal documents)
    if ocr_arabic_chars > direct_arabic_chars:
        logging.info(f"OCR extraction yielded more Arabic content ({ocr_arabic_chars} vs {direct_arabic_chars} chars)")
        best_text = ocr_text
        best_method = "OCR"
    else:
        logging.info(f"Direct extraction yielded more Arabic content ({direct_arabic_chars} vs {ocr_arabic_chars} chars)")
        best_text = direct_text
        best_method = "Direct"
    
    # Save individual results
    with open("output_chars_count.txt", "w", encoding="utf-8") as f:
        f.write(f"Direct extraction: {direct_chars} total chars, {direct_arabic_chars} Arabic chars\n")
        f.write(f"OCR extraction: {ocr_chars} total chars, {ocr_arabic_chars} Arabic chars\n")
        f.write(f"Recommended method: {best_method}\n")

    with open("output_direct.txt", "w", encoding="utf-8") as f:
        f.write(direct_text)

    with open("output_ocr.txt", "w", encoding="utf-8") as f:
        f.write(ocr_text)

    # Save best combined result
    with open("output_best.txt", "w", encoding="utf-8") as f:
        f.write(f"=== {best_method.upper()} EXTRACTION RESULTS ===\n\n")
        f.write(best_text)

    logging.info(f"Extraction finished!")
    logging.info(f"Direct: {direct_chars} chars ({direct_arabic_chars} Arabic)")
    logging.info(f"OCR: {ocr_chars} chars ({ocr_arabic_chars} Arabic)")
    logging.info(f"Best method: {best_method}")
    logging.info("Results saved to output_direct.txt, output_ocr.txt, and output_best.txt")


if __name__ == "__main__":
    main()
