"""
Test script with authentication for your actual saudi_labor_law.json file
"""

import requests
import json

def test_upload_with_auth():
    """Test the actual upload with your file and authentication."""
    
    base_url = "http://192.168.100.13:8000"
    file_path = "data_set/files/saudi_labor_law.json"
    
    # Your authentication token
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJsZWdhdG9vQGFsdGhvbWFsaWxhd2Zpcm0uc2EiLCJyb2xlIjoic3VwZXJfYWRtaW4iLCJleHAiOjE3NjEyMTQ0MjB9.3uSo04gNoPZD1nv2VrdRfthedoVr8_RcIDIJY3gAyZI"
    
    print("📤 Testing actual upload with authentication...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'title': 'نظام العمل السعودي',
                'category': 'law',
                'uploaded_by': 1
            }
            headers = {
                'Authorization': f'Bearer {auth_token}'
            }
            
            response = requests.post(
                f"{base_url}/api/v1/documents/upload",
                files=files,
                data=data,
                headers=headers
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Document ID: {result['data']['document_id']}")
            print(f"Chunks created: {result['data']['chunks_created']}")
            print(f"Law sources processed: {result['data']['law_sources_processed']}")
            print(f"Articles processed: {result['data']['articles_processed']}")
            print(f"Processing time: {result['data']['processing_time_seconds']} seconds")
            print(f"File size: {result['data']['file_size_bytes']} bytes")
            print(f"Duplicate detected: {result['data']['duplicate_detected']}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_upload_with_auth()
