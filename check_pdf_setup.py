#!/usr/bin/env python
"""
Script to verify PDF conversion setup for contract generation.
Checks for LibreOffice, Microsoft Word, and required Python packages.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def check_libreoffice():
    """Check if LibreOffice is installed."""
    print("Checking for LibreOffice...")
    
    if platform.system() == "Windows":
        paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    else:
        # Check if libreoffice command is available
        try:
            result = subprocess.run(
                ["which", "libreoffice"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ LibreOffice found at: {result.stdout.strip()}")
                return True
        except:
            pass
        paths = []
    
    for path in paths:
        if os.path.exists(path):
            print(f"✅ LibreOffice found at: {path}")
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0] if result.stdout else "Unknown version"
                    print(f"   Version: {version}")
            except:
                pass
            return True
    
    print("❌ LibreOffice not found")
    return False

def check_microsoft_word():
    """Check if Microsoft Word is available via COM (Windows only)."""
    if platform.system() != "Windows":
        print("⚠️  Microsoft Word check skipped (Windows only)")
        return False
    
    print("Checking for Microsoft Word...")
    try:
        import win32com.client
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            version = word.Version
            word.Quit()
            print(f"✅ Microsoft Word found (version {version})")
            print("   Note: docx2pdf can use Word via COM")
            return True
        except Exception as e:
            print(f"❌ Microsoft Word not accessible: {str(e)}")
            return False
    except ImportError:
        print("⚠️  Cannot check for Word (pywin32 not installed)")
        print("   docx2pdf uses COM which requires Word to be installed")
        return None

def check_python_packages():
    """Check if required Python packages are installed."""
    print("\nChecking Python packages...")
    
    packages = {
        "docxtpl": "DOCX template rendering",
        "docx2pdf": "DOCX to PDF conversion",
        "weasyprint": "HTML to PDF conversion",
        "python-docx": "DOCX file manipulation",
    }
    
    all_installed = True
    for package, description in packages.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} installed ({description})")
        except ImportError:
            print(f"❌ {package} NOT installed ({description})")
            all_installed = False
        except Exception as e:
            # Handle other import errors (like WeasyPrint missing system dependencies)
            print(f"⚠️  {package} installed but has issues: {str(e)[:100]}")
            # Don't fail completely if it's WeasyPrint (only needed for HTML templates)
            if package != "weasyprint":
                all_installed = False
    
    return all_installed

def test_conversion():
    """Test if PDF conversion actually works."""
    print("\nTesting PDF conversion...")
    
    try:
        from docx import Document
        import tempfile
        
        # Create a test DOCX
        doc = Document()
        doc.add_paragraph("Test document for PDF conversion")
        
        temp_docx = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        doc.save(temp_docx.name)
        temp_docx.close()
        
        pdf_path = temp_docx.name.replace(".docx", ".pdf")
        
        # Try conversion
        try:
            from docx2pdf import convert
            convert(temp_docx.name, pdf_path)
            if os.path.exists(pdf_path):
                print("✅ PDF conversion test successful!")
                os.unlink(temp_docx.name)
                os.unlink(pdf_path)
                return True
            else:
                print("❌ PDF conversion test failed: PDF file not created")
        except Exception as e:
            print(f"❌ PDF conversion test failed: {str(e)}")
        
        # Cleanup
        if os.path.exists(temp_docx.name):
            os.unlink(temp_docx.name)
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
        
        return False
        
    except Exception as e:
        print(f"❌ Test setup failed: {str(e)}")
        return False

def main():
    """Main verification function."""
    print("=" * 60)
    print("PDF Conversion Setup Verification")
    print("=" * 60)
    print()
    
    has_libreoffice = check_libreoffice()
    word_status = check_microsoft_word()
    packages_ok = check_python_packages()
    
    print()
    print("=" * 60)
    print("Summary & Recommendations")
    print("=" * 60)
    
    if has_libreoffice or word_status:
        print("✅ System dependencies: OK")
        if packages_ok:
            print("✅ Python packages: OK")
            print("\n🎉 Your setup looks good! PDF conversion should work.")
            test_conversion()
        else:
            print("❌ Python packages: Missing")
            print("\n⚠️  Please install missing packages:")
            print("   pip install -r requirements.txt")
    else:
        print("❌ System dependencies: Missing")
        print("\n📋 To fix PDF conversion, you need to install:")
        print()
        print("Option 1: LibreOffice (Recommended)")
        print("   - Download from: https://www.libreoffice.org/download/")
        print("   - Install to default location")
        print("   - Restart your Python application after installation")
        print()
        if platform.system() == "Windows":
            print("Option 2: Microsoft Word")
            print("   - Already installed? Make sure it's accessible")
            print("   - docx2pdf will use it via COM automatically")
        print()
        print("Then install Python packages:")
        print("   pip install -r requirements.txt")
    
    print()

if __name__ == "__main__":
    main()
