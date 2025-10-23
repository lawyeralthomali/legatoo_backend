"""
Test script to debug the document upload issue
"""

import requests
import json

def test_debug_endpoint():
    """Test the debug endpoint to see what's in the JSON file."""
    
    base_url = "http://192.168.100.13:8000"
    
    print("🔍 Testing debug endpoint...")
    
    try:
        # Test with the sample JSON file
        with open('saudi_labor_law.json', 'rb') as f:
            files = {'file': f}
            
            response = requests.post(
                f"{base_url}/api/v1/documents/debug-upload",
                files=files
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Debug analysis successful!")
            print(json.dumps(result['data'], indent=2, ensure_ascii=False))
        else:
            print(f"❌ Debug failed: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_upload_with_debug():
    """Test the actual upload after debug."""
    
    base_url = "http://192.168.100.13:8000"
    
    print("\n📤 Testing actual upload...")
    
    try:
        with open('saudi_labor_law.json', 'rb') as f:
            files = {'file': f}
            data = {
                'title': 'قانون العمل السعودي - اختبار',
                'category': 'law',
                'uploaded_by': 1
            }
            
            response = requests.post(
                f"{base_url}/api/v1/documents/upload",
                files=files,
                data=data
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Document ID: {result['data']['document_id']}")
            print(f"Chunks created: {result['data']['chunks_created']}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_debug_endpoint()
    test_upload_with_debug()
