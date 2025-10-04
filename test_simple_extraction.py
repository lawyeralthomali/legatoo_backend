#!/usr/bin/env python3
"""
Simple test for Arabic PDF extraction functionality.
Tests the individual extraction methods without the full app structure.
"""

import logging
import fitz
import pytesseract
from pdf2image import convert_from_path
import arabic_reshaper
from bidi.algorithm import get_display

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def needs_fixing(text):
    """Check if Arabic text needs fixing."""
    if not text.strip():
        return False
    words = text.split()
    avg_word_count = sum(len(w) for w in words) / max(len(words), 1)
    return avg_word_count <= 2

def fix_arabic_text(text):
    """Apply reshape + bidi to Arabic text."""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception as e:
        print(f"Arabic text fixing failed: {e}")
        return text

def extract_text_direct(pdf_path):
    """Direct extraction using PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page in doc:
            page_text = page.get_text("blocks")
            if page_text:
                blocks_text = "\n".join([block[4] for block in page_text if block[4].strip()])
                if blocks_text.strip():
                    text += blocks_text + "\n"
        
        doc.close()
        
        if needs_fixing(text):
            text = fix_arabic_text(text)
        
        return text
        
    except Exception as e:
        print(f"Direct extraction failed: {e}")
        return ""

def test_pdf_files():
    """Test PDF extraction on available files."""
    
    test_files = [
        "test_extracted_text/test.pdf",
        "test_extracted_text/test2.pdf"
    ]
    
    for pdf_path in test_files:
        from pathlib import Path
        if not Path(pdf_path).exists():
            print(f"❌ Test file not found: {pdf_path}")
            continue
            
        print(f"\n🔄 Testing: {pdf_path}")
        
        # Test direct extraction
        extracted_text = extract_text_direct(pdf_path)
        
        if extracted_text:
            print(f"✅ Successfully extracted {len(extracted_text)} characters")
            print(f"📄 Preview: {extracted_text[:100]}...")
        else:
            print(f"❌ Failed to extract text")

if __name__ == "__main__":
    test_pdf_files()

