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
    يحدد إذا النص يحتاج إصلاح (reshape + bidi) أو لا.
    القاعدة البسيطة: إذا النص يحتوي على أحرف عربية منفصلة (مسافات بين كل حرف)،
    أو إذا اتجاهه واضح إنه معكوس → يحتاج إصلاح.
    """
    if not text.strip():
        return False

    # مثال بسيط: إذا عدد المسافات كبير نسبة للحروف → النص غالباً متقطع
    words = text.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    return avg_word_len <= 2  # إذا الكلمات قصيرة جداً (حرفين أو أقل) → غالباً متقطعة


def fix_arabic_text(text: str) -> str:
    """تطبيق reshape + bidi"""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


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
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        text = ""
        for i, page in enumerate(pages):
            logging.info(f"OCR processing page {i+1}/{len(pages)}...")
            page_text = pytesseract.image_to_string(
                page, lang="ara", config="--oem 3 --psm 6"
            )
            if needs_fixing(page_text):
                page_text = fix_arabic_text(page_text)
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
