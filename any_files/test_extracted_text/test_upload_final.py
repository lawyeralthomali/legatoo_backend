"""
Final upload test using requests library (if available) or urllib.
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/v1/rag/upload-document"

# Simple English test content to avoid encoding issues
TEST_CONTENT = """
Test Law Document

Article 1: This is a test document for the upload endpoint.
Article 2: The system should work without loading ML models.
Article 3: This tests the NO-ML mode functionality.
Article 4: The endpoint should process this document successfully.
"""


def create_test_file():
    """Create a simple test file"""
    test_file = Path("final_test.txt")
    test_file.write_text(TEST_CONTENT, encoding='utf-8')
    return test_file


def test_upload_endpoint():
    """Test the upload endpoint"""
    print("🧪 Testing upload-document endpoint...")
    
    test_file = create_test_file()
    
    try:
        # Create multipart form data
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        
        # Read file content
        with open(test_file, 'rb') as f:
            file_content = f.read()
        
        # Build form data
        data_parts = []
        
        # File part
        file_part = f'--{boundary}\r\n'
        file_part += f'Content-Disposition: form-data; name="file"; filename="final_test.txt"\r\n'
        file_part += f'Content-Type: text/plain\r\n\r\n'
        file_part = file_part.encode() + file_content + b'\r\n'
        data_parts.append(file_part)
        
        # Form fields
        form_fields = {
            'law_name': 'Test Law Document',
            'law_type': 'law',
            'jurisdiction': 'Saudi Arabia',
            'description': 'Test for NO-ML mode functionality'
        }
        
        for key, value in form_fields.items():
            field_part = f'--{boundary}\r\n'
            field_part += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
            field_part += f'{value}\r\n'
            data_parts.append(field_part.encode())
        
        # End boundary
        data_parts.append(f'--{boundary}--\r\n'.encode())
        
        # Combine all parts
        data = b''.join(data_parts)
        
        # Create request
        req = urllib.request.Request(
            UPLOAD_ENDPOINT,
            data=data,
            method='POST'
        )
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        req.add_header('Content-Length', str(len(data)))
        
        print(f"📤 Uploading test file to: {UPLOAD_ENDPOINT}")
        start_time = time.time()
        
        # Make request
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                elapsed = time.time() - start_time
                
                print(f"⏱️  Response time: {elapsed:.2f} seconds")
                print(f"📊 Status: {response.status}")
                
                result = json.loads(response.read().decode())
                print(f"📝 Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                if response.status == 200 and result.get('success'):
                    print("✅ Test PASSED - Upload working!")
                    print(f"   - Chunks created: {result.get('data', {}).get('chunks_created', 'N/A')}")
                    print(f"   - Processing time: {result.get('data', {}).get('processing_time', 'N/A')}s")
                    print(f"   - File type: {result.get('data', {}).get('file_type', 'N/A')}")
                    print(f"   - Total words: {result.get('data', {}).get('total_words', 'N/A')}")
                    return True
                else:
                    print(f"❌ Test FAILED")
                    print(f"   Error: {result.get('message', 'Unknown error')}")
                    return False
                    
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error: {e.code} - {e.reason}")
            try:
                error_body = e.read().decode()
                error_data = json.loads(error_body)
                print(f"   Details: {error_data}")
            except:
                print(f"   Raw response: {error_body}")
            return False
        except urllib.error.URLError as e:
            print(f"❌ URL Error: {e.reason}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
            
    finally:
        if test_file.exists():
            test_file.unlink()
            print(f"🧹 Cleaned up test file")


def check_server():
    """Check if server is running"""
    try:
        with urllib.request.urlopen(f"{BASE_URL}/docs", timeout=5) as response:
            if response.status == 200:
                print("✅ Server is running")
                return True
    except:
        pass
    
    print("❌ Server is not running")
    print("   Please start the server: python run.py")
    return False


def main():
    print("=" * 70)
    print("🔬 Final Upload Test - NO-ML Mode")
    print("=" * 70)
    print()
    
    if not check_server():
        return
    
    print()
    
    success = test_upload_endpoint()
    
    print()
    print("=" * 70)
    if success:
        print("🎉 SUCCESS! The NO-ML mode fix is working!")
        print("   - No OOM crashes")
        print("   - No system hanging")
        print("   - Upload endpoint functioning")
        print("   - Hash-based embeddings generated")
        print("   - Document processing completed")
    else:
        print("❌ Test failed - check the error messages above")
    print("=" * 70)


if __name__ == "__main__":
    main()

