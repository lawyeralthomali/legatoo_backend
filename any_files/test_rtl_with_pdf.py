#!/usr/bin/env python3
"""
Test script to upload the Arabic PDF and test RTL text processing.

This script will:
1. Upload the attached Arabic PDF file
2. Test the RTL text processing
3. Show the extracted text results
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_rtl_processing():
    """Test RTL processing with the Arabic PDF file."""
    
    print("🧪 Testing RTL Processing with Arabic PDF")
    print("=" * 50)
    
    # Check if the PDF file exists
    pdf_file_path = "لائحة عمل لجنة المراجعة.pdf"
    
    if not os.path.exists(pdf_file_path):
        print(f"❌ PDF file not found: {pdf_file_path}")
        print("Please make sure the PDF file is in the current directory")
        return
    
    print(f"✅ Found PDF file: {pdf_file_path}")
    print(f"   File size: {os.path.getsize(pdf_file_path)} bytes")
    
    # You'll need to replace this with actual credentials
    auth_headers = {
        "Authorization": "Bearer YOUR_JWT_TOKEN_HERE"  # Replace with actual token
    }
    
    print(f"\n📁 Step 1: Upload Arabic PDF Document")
    print("-" * 30)
    
    # Upload the PDF file
    upload_url = f"{API_BASE}/legal-assistant/documents/upload"
    
    upload_data = {
        "title": "لائحة عمل لجنة المراجعة",  # Arabic title
        "document_type": "regulation",
        "language": "ar",  # Arabic language
        "notes": "Test document for RTL text processing",
        "process_immediately": True
    }
    
    try:
        with open(pdf_file_path, 'rb') as f:
            files = {"file": (pdf_file_path, f, "application/pdf")}
            response = requests.post(
                upload_url,
                data=upload_data,
                files=files,
                headers=auth_headers
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                document_id = result["data"]["id"]
                print(f"✅ Document uploaded successfully!")
                print(f"   Document ID: {document_id}")
                print(f"   Title: {result['data']['title']}")
                print(f"   Language: {result['data']['language']}")
                print(f"   File: {result['data']['file_path']}")
                
                # Wait for processing to complete
                print(f"\n⏳ Waiting for document processing to complete...")
                time.sleep(15)  # Wait 15 seconds for processing
                
                print(f"\n📄 Step 2: Check RTL Text Processing Results")
                print("-" * 30)
                
                # Check the extracted text files
                debug_url = f"{API_BASE}/legal-assistant/debug/extracted-text/{document_id}"
                
                response = requests.get(debug_url, headers=auth_headers)
                
                if response.status_code == 200:
                    debug_result = response.json()
                    if debug_result.get("success"):
                        files_data = debug_result["data"]["files"]
                        
                        print(f"✅ Retrieved {len(files_data)} extracted text files:")
                        print(f"   Document: {debug_result['data']['document_title']}")
                        print(f"   Language: {debug_result['data']['document_language']}")
                        print(f"   Directory: {debug_result['data']['extracted_text_directory']}")
                        
                        for file_info in files_data:
                            if 'content_preview' in file_info:
                                print(f"\n📋 {file_info['file_type'].upper()} TEXT:")
                                print(f"   File: {file_info['filename']}")
                                print(f"   Size: {file_info.get('size_bytes', 0)} bytes")
                                print(f"   Characters: {file_info.get('character_count', 0)}")
                                print(f"   Words: {file_info.get('word_count', 0)}")
                                
                                # Show a sample of the content
                                preview = file_info['content_preview'][:500]
                                print(f"\n   Sample (first 500 chars):")
                                print(f"   {'-' * 40}")
                                print(f"   {preview}")
                                if len(file_info['content_preview']) > 500:
                                    print(f"   ... (truncated)")
                                print(f"   {'-' * 40}")
                                
                                # Check if RTL processing is working
                                if file_info['file_type'] == 'raw':
                                    print(f"\n   🔍 RTL Analysis:")
                                    # Check for common Arabic patterns
                                    if 'لائحة' in preview or 'لجنة' in preview or 'المراجعة' in preview:
                                        print(f"   ✅ Arabic text detected")
                                        
                                        # Check if text direction looks correct
                                        if preview.startswith('لائحة') or 'لائحة' in preview[:50]:
                                            print(f"   ✅ Text appears to be in correct RTL direction")
                                        else:
                                            print(f"   ⚠️  Text direction may still need adjustment")
                                    else:
                                        print(f"   ⚠️  Arabic text not clearly detected in preview")
                        
                        print(f"\n🎯 Step 3: Manual File Check")
                        print("-" * 30)
                        
                        # Check the actual files on disk
                        extracted_text_dir = Path("uploads/extracted_text")
                        expected_files = [
                            f"document_{document_id}_raw.txt",
                            f"document_{document_id}_cleaned.txt", 
                            f"document_{document_id}_chunks.txt"
                        ]
                        
                        print(f"Checking files in {extracted_text_dir}:")
                        for filename in expected_files:
                            file_path = extracted_text_dir / filename
                            if file_path.exists():
                                print(f"   ✅ {filename} exists")
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        # Read first few lines after header
                                        lines = f.readlines()
                                        # Skip header lines (first 6 lines)
                                        if len(lines) > 6:
                                            first_content_line = lines[6].strip()
                                            print(f"      First content: {first_content_line[:100]}...")
                                except Exception as e:
                                    print(f"      Error reading: {e}")
                            else:
                                print(f"   ❌ {filename} not found")
                        
                        print(f"\n🎉 RTL Test completed!")
                        print(f"   Check the extracted text files to verify RTL processing")
                        print(f"   Arabic text should now display correctly from right to left")
                        
                    else:
                        print(f"❌ Debug endpoint error: {debug_result.get('message')}")
                else:
                    print(f"❌ Debug endpoint failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                
            else:
                print(f"❌ Upload failed: {result.get('message')}")
                if 'errors' in result:
                    for error in result['errors']:
                        print(f"   Error: {error.get('message')}")
        else:
            print(f"❌ Upload request failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def show_instructions():
    """Show instructions for testing RTL processing."""
    
    print("\n📖 RTL Testing Instructions")
    print("=" * 50)
    
    print(f"\n🔧 Before Testing:")
    print(f"   1. Make sure your server is running: {BASE_URL}")
    print(f"   2. Replace 'YOUR_JWT_TOKEN_HERE' with a valid JWT token")
    print(f"   3. Ensure the PDF file 'لائحة عمل لجنة المراجعة.pdf' is in the current directory")
    
    print(f"\n📋 Expected Results:")
    print(f"   - Document should upload successfully")
    print(f"   - Arabic text should be extracted correctly")
    print(f"   - Text should display in proper RTL direction")
    print(f"   - Extracted files should be created in uploads/extracted_text/")
    
    print(f"\n🔍 What to Look For:")
    print(f"   - Title should be: 'لائحة عمل لجنة المراجعة'")
    print(f"   - Text should read from right to left")
    print(f"   - Arabic letters should be properly connected")
    print(f"   - No backwards text display")
    
    print(f"\n🔄 If RTL is Still Wrong:")
    print(f"   1. Restart your server to apply the bidirectional processing fix")
    print(f"   2. The fix is already implemented in the code")
    print(f"   3. Server restart is needed to activate the changes")

if __name__ == "__main__":
    print("🔍 RTL Processing Test with Arabic PDF")
    print("=" * 50)
    
    show_instructions()
    
    print(f"\n⚠️  To run the actual test:")
    print(f"   1. Replace 'YOUR_JWT_TOKEN_HERE' with a valid JWT token")
    print(f"   2. Make sure the PDF file is in the current directory")
    print(f"   3. Run: python test_rtl_with_pdf.py")
    
    # Uncomment the line below to run the actual test
    # test_rtl_processing()




