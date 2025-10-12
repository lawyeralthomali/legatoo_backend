"""
Test script to verify the upload-document endpoint fix.

This tests that:
1. The endpoint doesn't hang
2. Embeddings are generated without blocking
3. The async operations work correctly
"""

import asyncio
import aiohttp
import time
import os
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/rag/upload-document"

# Create a sample test file
TEST_FILE_CONTENT = """
نظام اختبار قصير

المادة الأولى: هذه مادة اختبارية للتحقق من عمل نظام المعالجة.

المادة الثانية: يجب أن يتم معالجة هذا النص بشكل صحيح وإنشاء embeddings له.

المادة الثالثة: هذا النص قصير كفاية لتجنب استهلاك موارد كثيرة.
"""


async def create_test_file():
    """Create a temporary test file"""
    test_file = Path("test_law_document.txt")
    test_file.write_text(TEST_FILE_CONTENT, encoding='utf-8')
    return test_file


async def test_upload_endpoint():
    """Test the upload endpoint"""
    print("🧪 Testing upload-document endpoint...")
    
    # Create test file
    test_file = await create_test_file()
    
    try:
        # Prepare the upload
        data = aiohttp.FormData()
        data.add_field('file',
                      open(test_file, 'rb'),
                      filename='test_law.txt',
                      content_type='text/plain')
        data.add_field('law_name', 'نظام اختبار')
        data.add_field('law_type', 'law')
        data.add_field('jurisdiction', 'السعودية')
        data.add_field('description', 'ملف اختبار للتحقق من الإصلاح')
        
        print(f"📤 Uploading test file: {test_file.name}")
        start_time = time.time()
        
        # Set a timeout to detect hanging
        timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes max
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(UPLOAD_ENDPOINT, data=data) as response:
                    elapsed = time.time() - start_time
                    
                    print(f"⏱️  Response received in {elapsed:.2f} seconds")
                    print(f"📊 Status: {response.status}")
                    
                    result = await response.json()
                    print(f"📝 Response: {result}")
                    
                    # Check for success
                    if response.status == 200 and result.get('success'):
                        print("✅ Test PASSED - Endpoint working correctly!")
                        print(f"   - Chunks created: {result.get('data', {}).get('chunks_created', 'N/A')}")
                        print(f"   - Processing time: {result.get('data', {}).get('processing_time', 'N/A')}s")
                        return True
                    else:
                        print(f"❌ Test FAILED - Unexpected response")
                        print(f"   Error: {result.get('message', 'Unknown error')}")
                        return False
                        
            except asyncio.TimeoutError:
                elapsed = time.time() - start_time
                print(f"❌ Test FAILED - Request timed out after {elapsed:.2f} seconds")
                print("   This suggests the endpoint is still hanging!")
                return False
                
            except aiohttp.ClientError as e:
                print(f"❌ Test FAILED - Connection error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Test FAILED - Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()
            print(f"🧹 Cleaned up test file")


async def check_server_status():
    """Check if server is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/docs") as response:
                if response.status == 200:
                    print("✅ Server is running")
                    return True
    except:
        pass
    
    print("❌ Server is not running or not accessible")
    print(f"   Please start the server first: python run.py")
    return False


async def main():
    """Main test function"""
    print("=" * 60)
    print("🔬 Testing Upload Document Endpoint Fix")
    print("=" * 60)
    print()
    
    # Check server status
    if not await check_server_status():
        return
    
    print()
    
    # Run test
    success = await test_upload_endpoint()
    
    print()
    print("=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Fix is working!")
    else:
        print("❌ TEST FAILED - Issue still exists or server error")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())



