#!/usr/bin/env python3
"""
PDF Extraction Diagnostic Tool

This script helps diagnose PDF extraction issues by testing all available methods.
Run this script to check if your PDF can be processed and which method works best.

Usage:
    python test_pdf_extraction.py path/to/your/document.pdf
"""

import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("=" * 80)
    print("CHECKING DEPENDENCIES")
    print("=" * 80)
    
    dependencies = {
        'PyMuPDF (fitz)': False,
        'pdfplumber': False,
        'PyPDF2': False,
        'pytesseract': False,
        'pdf2image': False,
        'Pillow': False
    }
    
    # Check PyMuPDF
    try:
        import fitz
        dependencies['PyMuPDF (fitz)'] = True
        print("✅ PyMuPDF (fitz) installed - version:", fitz.version)
    except ImportError:
        print("❌ PyMuPDF not installed - run: pip install PyMuPDF")
    
    # Check pdfplumber
    try:
        import pdfplumber
        dependencies['pdfplumber'] = True
        print("✅ pdfplumber installed")
    except ImportError:
        print("❌ pdfplumber not installed - run: pip install pdfplumber")
    
    # Check PyPDF2
    try:
        import PyPDF2
        dependencies['PyPDF2'] = True
        print("✅ PyPDF2 installed - version:", PyPDF2.__version__)
    except ImportError:
        print("❌ PyPDF2 not installed - run: pip install PyPDF2")
    
    # Check pytesseract
    try:
        import pytesseract
        dependencies['pytesseract'] = True
        print("✅ pytesseract installed")
        
        # Check Tesseract executable
        try:
            version = pytesseract.get_tesseract_version()
            print(f"   Tesseract version: {version}")
            
            # Check languages
            langs = pytesseract.get_languages()
            print(f"   Available languages: {', '.join(langs)}")
            if 'ara' in langs:
                print("   ✅ Arabic OCR supported")
            else:
                print("   ⚠️  Arabic OCR not available - install: sudo apt-get install tesseract-ocr-ara")
        except Exception as e:
            print(f"   ⚠️  Tesseract executable not found: {e}")
            print("   Install: sudo apt-get install tesseract-ocr tesseract-ocr-ara")
    except ImportError:
        print("❌ pytesseract not installed - run: pip install pytesseract")
    
    # Check pdf2image
    try:
        import pdf2image
        dependencies['pdf2image'] = True
        print("✅ pdf2image installed")
    except ImportError:
        print("❌ pdf2image not installed - run: pip install pdf2image")
    
    # Check Pillow
    try:
        from PIL import Image
        dependencies['Pillow'] = True
        print("✅ Pillow (PIL) installed")
    except ImportError:
        print("❌ Pillow not installed - run: pip install Pillow")
    
    print()
    return dependencies


def test_pdf_info(pdf_path: str):
    """Get basic PDF information."""
    print("=" * 80)
    print("PDF INFORMATION")
    print("=" * 80)
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        print(f"📄 File: {pdf_path}")
        print(f"📊 Pages: {len(doc)}")
        print(f"📏 File size: {os.path.getsize(pdf_path) / 1024:.2f} KB")
        
        # Check metadata
        metadata = doc.metadata
        if metadata:
            print("\n📋 Metadata:")
            for key, value in metadata.items():
                if value:
                    print(f"   {key}: {value}")
        
        doc.close()
        print()
        return True
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return False


def test_direct_extraction(pdf_path: str):
    """Test direct text extraction using PyMuPDF."""
    print("=" * 80)
    print("TEST 1: DIRECT EXTRACTION (PyMuPDF)")
    print("=" * 80)
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        total_text = ""
        
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            total_text += text
            print(f"Page {page_num}: {len(text)} characters")
        
        doc.close()
        
        total_chars = len(total_text)
        stripped_chars = len(total_text.strip())
        arabic_chars = sum(1 for c in total_text if '\u0600' <= c <= '\u06FF')
        
        print(f"\n📊 Results:")
        print(f"   Total characters: {total_chars}")
        print(f"   Stripped characters: {stripped_chars}")
        print(f"   Arabic characters: {arabic_chars}")
        print(f"   Arabic ratio: {arabic_chars/total_chars*100:.1f}%" if total_chars > 0 else "   Arabic ratio: 0%")
        
        if stripped_chars > 0:
            print(f"✅ Direct extraction SUCCESSFUL")
            print(f"\n📝 First 500 characters:")
            print("-" * 80)
            print(total_text[:500])
            print("-" * 80)
            return total_text
        else:
            print(f"⚠️  Direct extraction returned EMPTY text")
            print("   This PDF likely contains only images (scanned document)")
            return ""
        
    except Exception as e:
        print(f"❌ Direct extraction FAILED: {e}")
        return ""


def test_enhanced_extraction(pdf_path: str):
    """Test enhanced Arabic PDF extraction."""
    print("\n" + "=" * 80)
    print("TEST 2: ENHANCED ARABIC EXTRACTION")
    print("=" * 80)
    
    try:
        from app.services.enhanced_arabic_pdf_processor import EnhancedArabicPDFProcessor
        
        processor = EnhancedArabicPDFProcessor()
        text, method = processor.extract_pdf_text(pdf_path, language='ar')
        
        total_chars = len(text)
        stripped_chars = len(text.strip())
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        
        print(f"\n📊 Results:")
        print(f"   Method used: {method}")
        print(f"   Total characters: {total_chars}")
        print(f"   Stripped characters: {stripped_chars}")
        print(f"   Arabic characters: {arabic_chars}")
        
        if stripped_chars > 0:
            print(f"✅ Enhanced extraction SUCCESSFUL")
            print(f"\n📝 First 500 characters:")
            print("-" * 80)
            print(text[:500])
            print("-" * 80)
            return text
        else:
            print(f"⚠️  Enhanced extraction returned EMPTY text")
            return ""
        
    except Exception as e:
        print(f"❌ Enhanced extraction FAILED: {e}")
        import traceback
        traceback.print_exc()
        return ""


def test_fallback_methods(pdf_path: str):
    """Test fallback extraction methods."""
    print("\n" + "=" * 80)
    print("TEST 3: FALLBACK METHODS")
    print("=" * 80)
    
    results = {}
    
    # Test pdfplumber
    print("\n🔍 Testing pdfplumber...")
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            
            results['pdfplumber'] = len(text.strip())
            print(f"   ✅ pdfplumber: {results['pdfplumber']} characters")
    except Exception as e:
        print(f"   ❌ pdfplumber failed: {e}")
        results['pdfplumber'] = 0
    
    # Test PyPDF2
    print("\n🔍 Testing PyPDF2...")
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            
            results['PyPDF2'] = len(text.strip())
            print(f"   ✅ PyPDF2: {results['PyPDF2']} characters")
    except Exception as e:
        print(f"   ❌ PyPDF2 failed: {e}")
        results['PyPDF2'] = 0
    
    print(f"\n📊 Fallback Results Summary:")
    for method, chars in results.items():
        status = "✅" if chars > 0 else "❌"
        print(f"   {status} {method}: {chars} characters")
    
    return results


def main():
    """Main diagnostic function."""
    print("\n" + "=" * 80)
    print("PDF EXTRACTION DIAGNOSTIC TOOL")
    print("=" * 80)
    print()
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_extraction.py path/to/your/document.pdf")
        print("\nExample:")
        print("  python test_pdf_extraction.py uploads/legal_documents/contract.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found: {pdf_path}")
        sys.exit(1)
    
    # Check dependencies
    deps = check_dependencies()
    
    # Test PDF info
    if not test_pdf_info(pdf_path):
        sys.exit(1)
    
    # Test extraction methods
    direct_text = test_direct_extraction(pdf_path)
    enhanced_text = test_enhanced_extraction(pdf_path)
    fallback_results = test_fallback_methods(pdf_path)
    
    # Final summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    all_failed = (
        len(direct_text.strip()) == 0 and
        len(enhanced_text.strip()) == 0 and
        all(v == 0 for v in fallback_results.values())
    )
    
    if all_failed:
        print("\n❌ ALL EXTRACTION METHODS FAILED")
        print("\n🔧 Recommended Actions:")
        print("   1. This PDF is likely image-based (scanned document)")
        print("   2. Install Tesseract OCR for scanned PDF support:")
        print("      Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-ara")
        print("      macOS: brew install tesseract tesseract-lang")
        print("      Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("   3. Install poppler-utils (required for OCR):")
        print("      Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("      macOS: brew install poppler")
        print("   4. Restart this diagnostic script")
    elif len(direct_text.strip()) > 100 or len(enhanced_text.strip()) > 100:
        print("\n✅ PDF CAN BE PROCESSED SUCCESSFULLY")
        print("\n📊 Best extraction method:")
        if len(enhanced_text) > len(direct_text):
            print("   Enhanced Arabic extraction")
        else:
            print("   Direct extraction")
        print("\n💡 Your PDF should work with the document upload endpoint")
    else:
        print("\n⚠️  PDF EXTRACTED BUT TEXT IS TOO SHORT")
        print(f"   Extracted: {max(len(direct_text.strip()), len(enhanced_text.strip()))} characters")
        print("   Minimum required: 100 characters (or 20 with warning)")
        print("\n🔧 Possible issues:")
        print("   - PDF may be mostly empty")
        print("   - PDF may contain mostly images")
        print("   - Consider installing Tesseract OCR for better results")
    
    print("\n" + "=" * 80)
    print("For more information, see: PDF_EXTRACTION_FIX.md")
    print("=" * 80)


if __name__ == "__main__":
    main()
