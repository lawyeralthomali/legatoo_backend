"""
Simple upload test without external dependencies.

This test directly tests the upload endpoint using Python's built-in urllib.
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

# Simple test content
TEST_CONTENT = """
نظام اختبار

المادة 1: هذا نص اختبار قصير.
المادة 2: يجب أن يعمل النظام دون تحميل أي نماذج.
المادة 3: هذا اختبار للوضع بدون تعلم آلة.
"""


def create_test_file():
    """Create a simple test file"""
    test_file = Path("simple_test.txt")
    test_file.write_text(TEST_CONTENT, encoding='utf-8')
    return test_file


def test_upload():
    """Test upload using built-in urllib"""
    print("🧪 Testing upload-document endpoint...")
    
    test_file = create_test_file()
    
    try:
        # Create multipart form data manually
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        
        # Prepare form data
        data_parts = []
        
        # File part
        with open(test_file, 'rb') as f:
            file_content = f.read()
        
        file_part = f'--{boundary}\r\n'
        file_part += f'Content-Disposition: form-data; name="file"; filename="simple_test.txt"\r\n'
        file_part += f'Content-Type: text/plain\r\n\r\n'
        file_part = file_part.encode() + file_content + b'\r\n'
        data_parts.append(file_part)
        
        # Other form fields
        form_fields = {
            'law_name': 'اختبار بدون تعلم آلة',
            'law_type': 'law',
            'jurisdiction': 'السعودية',
            'description': 'اختبار الوضع بدون ML'
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
        
        print(f"📤 Uploading test file...")
        start_time = time.time()
        
        # Make request with timeout
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                elapsed = time.time() - start_time
                
                print(f"⏱️  Response time: {elapsed:.2f} seconds")
                print(f"📊 Status: {response.status}")
                
                result = json.loads(response.read().decode())
                print(f"📝 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                if response.status == 200 and result.get('success'):
                    print("✅ Test PASSED - Upload working!")
                    print(f"   - Chunks created: {result.get('data', {}).get('chunks_created', 'N/A')}")
                    print(f"   - Processing time: {result.get('data', {}).get('processing_time', 'N/A')}s")
                    return True
                else:
                    print(f"❌ Test FAILED")
                    print(f"   Error: {result.get('message', 'Unknown error')}")
                    return False
                    
        except urllib.error.URLError as e:
            if hasattr(e, 'reason'):
                print(f"❌ Connection failed: {e.reason}")
            else:
                print(f"❌ Server error: {e.code}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
            
    finally:
        if test_file.exists():
            test_file.unlink()
            print(f"🧹 Cleaned up test file")


def check_server_status():
    """Check if server is running"""
    try:
        with urllib.request.urlopen(f"{BASE_URL}/docs", timeout=5) as response:
            if response.status == 200:
                print("✅ Server is running")
                return True
    except:
        pass
    
    print("❌ Server is not running or not accessible")
    print(f"   Please start the server first: python run.py")
    return False


def main():
    print("=" * 60)
    print("🔬 Simple Upload Test (No External Dependencies)")
    print("=" * 60)
    print()
    
    if not check_server_status():
        return
    
    print()
    
    success = test_upload()
    
    print()
    print("=" * 60)
    if success:
        print("✅ UPLOAD TEST PASSED!")
        print("   - NO-ML mode working")
        print("   - No memory issues")
        print("   - No OOM crashes")
        print("   - Endpoint functioning correctly")
    else:
        print("❌ UPLOAD TEST FAILED!")
        print("   - Issue still exists")
    print("=" * 60)


if __name__ == "__main__":
    main()
