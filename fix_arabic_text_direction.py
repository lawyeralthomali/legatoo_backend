#!/usr/bin/env python3
"""
Script to fix Arabic text direction issues and reprocess documents.

This script demonstrates how to:
1. Fix the Arabic text direction issue in the codebase
2. Reprocess an existing document to see the corrected text
3. Compare before/after results

Usage:
    python fix_arabic_text_direction.py
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_arabic_text_fix():
    """Test the Arabic text direction fix."""
    
    print("🔧 Testing Arabic Text Direction Fix")
    print("=" * 50)
    
    # You'll need to replace these with actual credentials
    auth_headers = {
        "Authorization": "Bearer YOUR_JWT_TOKEN_HERE"  # Replace with actual token
    }
    
    document_id = 1  # The document we saw in the extracted_text folder
    
    print(f"\n📄 Step 1: Reprocess Document {document_id}")
    print("-" * 30)
    
    # Reprocess the document to apply the fix
    reprocess_url = f"{API_BASE}/legal-assistant/documents/{document_id}/reprocess"
    
    try:
        response = requests.post(reprocess_url, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Document reprocessing started!")
                print(f"   Document ID: {document_id}")
                print(f"   Status: {result['data']['status']}")
                
                # Wait for processing to complete
                print(f"\n⏳ Waiting for reprocessing to complete...")
                time.sleep(15)  # Wait 15 seconds for processing
                
                print(f"\n📄 Step 2: Check Updated Extracted Text")
                print("-" * 30)
                
                # Check the updated extracted text files
                debug_url = f"{API_BASE}/legal-assistant/debug/extracted-text/{document_id}"
                
                response = requests.get(debug_url, headers=auth_headers)
                
                if response.status_code == 200:
                    debug_result = response.json()
                    if debug_result.get("success"):
                        files_data = debug_result["data"]["files"]
                        
                        print(f"✅ Retrieved updated extracted text files:")
                        print(f"   Document: {debug_result['data']['document_title']}")
                        print(f"   Language: {debug_result['data']['document_language']}")
                        
                        for file_info in files_data:
                            if 'content_preview' in file_info:
                                print(f"\n📋 {file_info['file_type'].upper()} TEXT (Updated):")
                                print(f"   File: {file_info['filename']}")
                                print(f"   Size: {file_info.get('size_bytes', 0)} bytes")
                                print(f"   Characters: {file_info.get('character_count', 0)}")
                                
                                # Show a sample of the corrected content
                                preview = file_info['content_preview'][:300]
                                print(f"\n   Sample (first 300 chars):")
                                print(f"   {'-' * 40}")
                                print(f"   {preview}")
                                print(f"   {'-' * 40}")
                                
                                # Check if the text direction is now correct
                                if 'ة عجارلما ةنجل لمع ةحئلا' in preview:
                                    print(f"   ✅ Arabic text direction appears to be corrected!")
                                else:
                                    print(f"   ⚠️  Arabic text direction may still need adjustment")
                        
                        print(f"\n🎯 Step 3: Compare with Original Files")
                        print("-" * 30)
                        
                        # Check if the original files still exist for comparison
                        extracted_text_dir = Path("uploads/extracted_text")
                        original_files = [
                            f"document_{document_id}_raw.txt",
                            f"document_{document_id}_cleaned.txt", 
                            f"document_{document_id}_chunks.txt"
                        ]
                        
                        print(f"Original files in {extracted_text_dir}:")
                        for filename in original_files:
                            file_path = extracted_text_dir / filename
                            if file_path.exists():
                                print(f"   ✅ {filename} exists")
                                # Show first line to compare
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        first_line = f.readline().strip()
                                        if first_line.startswith('==='):
                                            # Skip header lines
                                            for _ in range(5):
                                                first_line = f.readline().strip()
                                        print(f"      First content line: {first_line[:50]}...")
                                except Exception as e:
                                    print(f"      Error reading: {e}")
                            else:
                                print(f"   ❌ {filename} not found")
                        
                        print(f"\n🎉 Test completed!")
                        print(f"   The Arabic text should now display in the correct direction.")
                        print(f"   Check the updated files to see the improvement.")
                        
                    else:
                        print(f"❌ Debug endpoint error: {debug_result.get('message')}")
                else:
                    print(f"❌ Debug endpoint failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                
            else:
                print(f"❌ Reprocessing failed: {result.get('message')}")
        else:
            print(f"❌ Reprocessing request failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def show_fix_explanation():
    """Show explanation of the Arabic text direction fix."""
    
    print("\n📖 Arabic Text Direction Fix Explanation")
    print("=" * 50)
    
    print("\n🔍 The Problem:")
    print("   - Arabic text was being extracted correctly from PDFs")
    print("   - But it was displaying in wrong direction (LTR instead of RTL)")
    print("   - This is common with PDF extraction tools")
    
    print("\n🔧 The Solution:")
    print("   1. Added bidirectional text processing immediately after extraction")
    print("   2. Applied complete Arabic preprocessing pipeline during cleaning")
    print("   3. Used python-bidi library to correct text direction")
    
    print("\n📝 Code Changes Made:")
    print("   1. Modified extract_text_from_file() to apply bidirectional processing")
    print("   2. Updated clean_text() to use preprocess_arabic_text() instead of normalize_arabic_text()")
    print("   3. Both changes ensure Arabic text displays correctly")
    
    print("\n🎯 Expected Results:")
    print("   - Arabic text should now read from right to left correctly")
    print("   - Text should be properly connected and formatted")
    print("   - Numbers and symbols should maintain correct order")
    
    print("\n🔄 To Apply the Fix:")
    print("   1. The code changes are already applied")
    print("   2. Reprocess existing documents using the reprocess endpoint")
    print("   3. New uploads will automatically use the corrected processing")

if __name__ == "__main__":
    print("🔧 Arabic Text Direction Fix Test")
    print("=" * 50)
    
    show_fix_explanation()
    
    print(f"\n⚠️  To run the actual test:")
    print(f"   1. Replace 'YOUR_JWT_TOKEN_HERE' with a valid JWT token")
    print(f"   2. Make sure your server is running on {BASE_URL}")
    print(f"   3. Run: python fix_arabic_text_direction.py")
    
    # Uncomment the line below to run the actual test
    # test_arabic_text_fix()




