#!/usr/bin/env python3
"""
Test script to demonstrate the extracted text saving functionality.

This script shows how to:
1. Upload a document via the API
2. View the extracted text files using the debug endpoint
3. See how Arabic text looks after processing

Usage:
    python test_extracted_text.py
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on different port
API_BASE = f"{BASE_URL}/api/v1"

def test_extracted_text_functionality():
    """Test the extracted text saving functionality."""
    
    print("🧪 Testing Extracted Text Functionality")
    print("=" * 50)
    
    # You'll need to replace these with actual credentials
    # For testing, you might want to create a test user first
    auth_headers = {
        "Authorization": "Bearer YOUR_JWT_TOKEN_HERE"  # Replace with actual token
    }
    
    print("\n📁 Step 1: Upload a document")
    print("-" * 30)
    
    # Example: Upload a PDF file
    upload_url = f"{API_BASE}/legal-assistant/documents/upload"
    
    # You'll need to provide an actual file path
    file_path = "path/to/your/arabic/document.pdf"  # Replace with actual file
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        print("Please provide a valid file path to test with.")
        return
    
    upload_data = {
        "title": "Test Arabic Document",
        "document_type": "contract",
        "language": "ar",
        "notes": "Test document for extracted text functionality",
        "process_immediately": True
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {"file": f}
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
                
                # Wait for processing to complete
                print(f"\n⏳ Waiting for document processing to complete...")
                time.sleep(10)  # Wait 10 seconds for processing
                
                print(f"\n📄 Step 2: View extracted text files")
                print("-" * 30)
                
                # Test the debug endpoint
                debug_url = f"{API_BASE}/legal-assistant/debug/extracted-text/{document_id}"
                
                # Get all files
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
                            print(f"\n📋 {file_info['file_type'].upper()} TEXT:")
                            print(f"   File: {file_info['filename']}")
                            print(f"   Size: {file_info.get('size_bytes', 0)} bytes")
                            print(f"   Characters: {file_info.get('character_count', 0)}")
                            print(f"   Words: {file_info.get('word_count', 0)}")
                            
                            if 'content_preview' in file_info:
                                print(f"\n   Preview (first 500 chars):")
                                print(f"   {'-' * 40}")
                                preview = file_info['content_preview'][:500]
                                print(f"   {preview}")
                                if len(file_info['content_preview']) > 500:
                                    print(f"   ... (truncated)")
                                print(f"   {'-' * 40}")
                        
                        print(f"\n🎯 Step 3: View specific file types")
                        print("-" * 30)
                        
                        # Test specific file types
                        for file_type in ["raw", "cleaned", "chunks"]:
                            specific_url = f"{debug_url}?file_type={file_type}"
                            response = requests.get(specific_url, headers=auth_headers)
                            
                            if response.status_code == 200:
                                result = response.json()
                                if result.get("success") and result["data"]["files"]:
                                    file_info = result["data"]["files"][0]
                                    print(f"✅ {file_type.upper()} file available:")
                                    print(f"   Size: {file_info.get('size_bytes', 0)} bytes")
                                    print(f"   Characters: {file_info.get('character_count', 0)}")
                                    
                                    # Show a sample of the content
                                    if 'content_preview' in file_info:
                                        sample = file_info['content_preview'][:200]
                                        print(f"   Sample: {sample}...")
                                else:
                                    print(f"❌ {file_type.upper()} file not found")
                            else:
                                print(f"❌ Error retrieving {file_type} file: {response.status_code}")
                        
                        print(f"\n🎉 Test completed successfully!")
                        print(f"   You can now see how Arabic text looks after:")
                        print(f"   - Raw extraction from PDF/DOCX")
                        print(f"   - Cleaning and normalization")
                        print(f"   - Chunking into searchable segments")
                        
                    else:
                        print(f"❌ Debug endpoint error: {debug_result.get('message')}")
                else:
                    print(f"❌ Debug endpoint failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                
            else:
                print(f"❌ Upload failed: {result.get('message')}")
        else:
            print(f"❌ Upload request failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def show_usage_instructions():
    """Show usage instructions for the new functionality."""
    
    print("\n📖 Usage Instructions")
    print("=" * 50)
    
    print("\n1. Upload a document:")
    print("   POST /api/v1/legal-assistant/documents/upload")
    print("   - Upload any PDF, DOCX, or image file")
    print("   - Set language='ar' for Arabic documents")
    print("   - Set process_immediately=true")
    
    print("\n2. View extracted text files:")
    print("   GET /api/v1/legal-assistant/debug/extracted-text/{document_id}")
    print("   - Shows all extracted text files (raw, cleaned, chunks)")
    print("   - Add ?file_type=raw to see only raw extraction")
    print("   - Add ?file_type=cleaned to see only cleaned text")
    print("   - Add ?file_type=chunks to see only chunked text")
    
    print("\n3. File locations:")
    print("   - Raw text: uploads/extracted_text/document_{id}_raw.txt")
    print("   - Cleaned text: uploads/extracted_text/document_{id}_cleaned.txt")
    print("   - Chunks: uploads/extracted_text/document_{id}_chunks.txt")
    
    print("\n4. Arabic text processing:")
    print("   - Raw extraction preserves original formatting")
    print("   - Cleaning normalizes Unicode and removes duplicates")
    print("   - Chunking splits into 300-500 word segments")
    print("   - All files are saved with UTF-8 encoding")

if __name__ == "__main__":
    print("🔍 Extracted Text Functionality Test")
    print("=" * 50)
    
    show_usage_instructions()
    
    print(f"\n⚠️  To run the actual test:")
    print(f"   1. Replace 'YOUR_JWT_TOKEN_HERE' with a valid JWT token")
    print(f"   2. Replace 'path/to/your/arabic/document.pdf' with actual file")
    print(f"   3. Make sure your server is running on {BASE_URL}")
    print(f"   4. Run: python test_extracted_text.py")
    
    # Uncomment the line below to run the actual test
    # test_extracted_text_functionality()




