#!/usr/bin/env python3
"""
Simple RTL test script without Unicode emojis.
"""

import requests
import json
import time
import os

def test_rtl_processing():
    """Test RTL processing with the Arabic PDF file."""
    
    print("RTL Test with Arabic PDF")
    print("=" * 40)
    
    # Check if the PDF file exists
    pdf_file_path = "لائحة عمل لجنة المراجعة.pdf"
    
    if not os.path.exists(pdf_file_path):
        print(f"PDF file not found: {pdf_file_path}")
        return
    
    print(f"Found PDF file: {pdf_file_path}")
    print(f"File size: {os.path.getsize(pdf_file_path):,} bytes")
    
    # Test server connectivity
    BASE_URL = "http://localhost:8000"
    
    try:
        print(f"\nTesting server connectivity...")
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"Server is running on {BASE_URL}")
        else:
            print(f"Server responded with status: {response.status_code}")
    except Exception as e:
        print(f"Server not accessible: {e}")
        print(f"Make sure your server is running on {BASE_URL}")
        return
    
    print(f"\nInstructions for Manual Testing:")
    print("-" * 30)
    print(f"1. Open your browser and go to: {BASE_URL}/docs")
    print(f"2. Find the endpoint: POST /api/v1/legal-assistant/documents/upload")
    print(f"3. Click 'Try it out'")
    print(f"4. Upload the file: {pdf_file_path}")
    print(f"5. Set the form data:")
    print(f"   - title: لائحة عمل لجنة المراجعة")
    print(f"   - document_type: regulation")
    print(f"   - language: ar")
    print(f"   - notes: Test RTL processing")
    print(f"   - process_immediately: true")
    print(f"6. Click 'Execute'")
    print(f"7. Note the document ID from the response")
    
    print(f"\nThen check the extracted text:")
    print(f"1. Go to: GET /api/v1/legal-assistant/debug/extracted-text/{{document_id}}")
    print(f"2. Replace {{document_id}} with the ID from step 7")
    print(f"3. Click 'Try it out' and 'Execute'")
    print(f"4. Check the 'files' array in the response")
    
    print(f"\nWhat to Look For:")
    print(f"- Raw text should show Arabic text in correct RTL direction")
    print(f"- Title should be: 'لائحة عمل لجنة المراجعة'")
    print(f"- Text should read from right to left, not backwards")
    print(f"- Arabic letters should be properly connected")
    
    print(f"\nImportant:")
    print(f"- If the server was running before our code changes, restart it first")
    print(f"- The bidirectional processing fix needs a server restart to take effect")
    print(f"- You can restart with: Ctrl+C then 'python run.py'")

def show_expected_results():
    """Show what the results should look like."""
    
    print(f"\nExpected Results:")
    print("=" * 40)
    
    print(f"\nCorrect RTL Text (After Fix):")
    print(f"   'لائحة عمل لجنة المراجعة'")
    print(f"   (Reads correctly from right to left)")
    
    print(f"\nWrong Direction (Before Fix):")
    print(f"   'ةعجارلما ةنجل لمع ةحئلا'")
    print(f"   (Reads backwards, left to right)")
    
    print(f"\nThe Fix Applied:")
    print(f"- Added bidirectional text processing after extraction")
    print(f"- Enhanced Arabic text cleaning with RTL processing")
    print(f"- Uses python-bidi library for proper text direction")

if __name__ == "__main__":
    test_rtl_processing()
    show_expected_results()
    
    print(f"\nNext Steps:")
    print(f"1. Restart your server if it was running before our changes")
    print(f"2. Use the Swagger UI to upload the PDF and test RTL processing")
    print(f"3. Check if Arabic text now displays in correct RTL direction")




