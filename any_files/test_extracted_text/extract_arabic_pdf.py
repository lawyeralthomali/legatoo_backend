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
    """Check if text contains Unicode artifacts that need cleaning"""
    if not text.strip():
        return False
    
    # Check for artifacts (isolated Unicode characters)
    artifacts = ['ﻢ', 'ﻪ', 'ﻆ', 'ﺍ', 'ﺕ', 'ﺏ', 'ﻞ', 'ﺝ', 'ﺡ', 'ﺥ', 'ﺩ', 'ﺫ', 'ﺭ', 'ﺯ', 'ﺱ', 'ﺵ', 'ﺹ', 'ﺽ', 'ﻁ', 'ﻅ', 'ﻉ', 'ﻍ', 'ﻑ', 'ﻕ', 'ﻙ', 'ﻝ', 'ﻡ', 'ﻥ', 'ﻩ', 'ﻭ', 'ﻱ']
    if any(artifact in text for artifact in artifacts):
        return True
    
    return False


def fix_arabic_text(text: str) -> str:
    """
    Clean Unicode artifacts from PDF text.
    NOTE: Direct extraction from PDF usually doesn't need BiDi/reshaping!
    Only clean artifacts, don't reverse the text.
    """
    if not text.strip():
        return text
    
    # Map of artifacts to correct Arabic characters
    artifacts_map = {
        # Alef forms
        'ﺍ': 'ا', 'ﺎ': 'ا', 'ﺀ': 'ء', 'ﺃ': 'أ', 'ﺈ': 'إ', 'ﺁ': 'آ',
        # Ba forms  
        'ﺏ': 'ب', 'ﺐ': 'ب', 'ﺑ': 'ب', 'ﺒ': 'ب',
        # Ta forms
        'ﺕ': 'ت', 'ﺖ': 'ت', 'ﺗ': 'ت', 'ﺘ': 'ت', 'ﺓ': 'ة', 'ﺔ': 'ة',
        # Jeem forms
        'ﺝ': 'ج', 'ﺞ': 'ج', 'ﺟ': 'ج', 'ﺠ': 'ج',
        # Ha forms
        'ﺡ': 'ح', 'ﺢ': 'ح', 'ﺣ': 'ح', 'ﺤ': 'ح',
        # Kha forms
        'ﺥ': 'خ', 'ﺦ': 'خ', 'ﺧ': 'خ', 'ﺨ': 'خ',
        # Dal forms
        'ﺩ': 'د', 'ﺪ': 'د', 'ﺫ': 'ذ', 'ﺬ': 'ذ',
        # Ra forms
        'ﺭ': 'ر', 'ﺮ': 'ر', 'ﺯ': 'ز', 'ﺰ': 'ز',
        # Seen forms
        'ﺱ': 'س', 'ﺲ': 'س', 'ﺳ': 'س', 'ﺴ': 'س', 'ﺵ': 'ش', 'ﺶ': 'ش', 'ﺷ': 'ش', 'ﺸ': 'ش',
        # Sad forms
        'ﺹ': 'ص', 'ﺺ': 'ص', 'ﺻ': 'ص', 'ﺼ': 'ص', 'ﺽ': 'ض', 'ﺾ': 'ض', 'ﺿ': 'ض', 'ﻀ': 'ض',
        # Ta forms (different)
        'ﻁ': 'ط', 'ﻂ': 'ط', 'ﻃ': 'ط', 'ﻄ': 'ط', 'ﻅ': 'ظ', 'ﻆ': 'ظ', 'ﻇ': 'ظ', 'ﻈ': 'ظ',
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
        'ﻭ': 'و', 'ﻮ': 'و',
        # Ya forms
        'ﻱ': 'ي', 'ﻲ': 'ي', 'ﻳ': 'ي', 'ﻴ': 'ي', 'ﺀ': 'ء', 'ﺁ': 'آ', 'ﺂ': 'آ',
        # Lam-Alef
        'ﻼ': 'لا', 'ﻻ': 'لا',
    }
    
    # Apply character mapping
    for artifact, correct_char in artifacts_map.items():
        text = text.replace(artifact, correct_char)
    
    # Remove excessive spaces
    text = ' '.join(text.split())
    
    return text


# ---------- [ استخراج النص مباشرة من PDF ] ----------
def extract_text_direct(pdf_path: str) -> str:
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            # نجرب "blocks" لأنه يعطي نتائج أوضح مع العربية
            page_text = page.get_text("blocks")
            if page_text:
                text += "\n".join([block[4] for block in page_text if block[4].strip()]) + "\n"
        doc.close()

        # لو النص فعلاً يحتاج إصلاح (متقطع/معكوس) → نصلحه
        if needs_fixing(text):
            text = fix_arabic_text(text)

        logging.info(f"[Direct] Extracted {len(text)} characters")
        return text
    except Exception as e:
        logging.error(f"Direct extraction failed: {e}")
        return ""


# ---------- [ استخراج النص بالـ OCR ] ----------
def extract_text_ocr(pdf_path: str) -> str:
    """OCR extraction - applies BiDi because OCR text is often backward"""
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        text = ""
        for i, page in enumerate(pages):
            logging.info(f"OCR processing page {i+1}/{len(pages)}...")
            page_text = pytesseract.image_to_string(
                page, lang="ara", config="--oem 3 --psm 6"
            )
            
            if page_text.strip():
                # Clean artifacts first
                if needs_fixing(page_text):
                    page_text = fix_arabic_text(page_text)
                
                # OCR text often needs BiDi/reshaping
                try:
                    reshaped = arabic_reshaper.reshape(page_text)
                    page_text = get_display(reshaped)
                except Exception as e:
                    logging.warning(f"BiDi processing failed: {e}")
                
                text += page_text + "\n"

        logging.info(f"[OCR] Extracted {len(text)} characters")
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

    # 1. Direct Extraction
    direct_text = extract_text_direct(pdf_path)
    with open("output_direct.txt", "w", encoding="utf-8") as f:
        f.write(direct_text)

    # 2. OCR Extraction
    ocr_text = extract_text_ocr(pdf_path)
    with open("output_ocr.txt", "w", encoding="utf-8") as f:
        f.write(ocr_text)

    logging.info("Extraction finished. Results saved to output_direct.txt and output_ocr.txt")


if __name__ == "__main__":
    main()