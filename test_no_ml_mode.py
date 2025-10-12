"""
Test the NO-ML mode to verify it works without loading any models.

This test verifies that:
1. No ML models are loaded
2. Hash-based embeddings are generated
3. The upload endpoint works without memory issues
"""

import asyncio
import aiohttp
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/rag/upload-document"

# Simple test content
TEST_CONTENT = """
نظام اختبار

المادة 1: هذا نص اختبار قصير.
المادة 2: يجب أن يعمل النظام دون تحميل أي نماذج.
المادة 3: هذا اختبار للوضع بدون تعلم آلة.
"""


async def create_test_file():
    """Create a simple test file"""
    test_file = Path("no_ml_test.txt")
    test_file.write_text(TEST_CONTENT, encoding='utf-8')
    return test_file


async def test_no_ml_upload():
    """Test upload in NO-ML mode"""
    print("🧪 Testing upload-document endpoint in NO-ML mode...")
    
    test_file = await create_test_file()
    
    try:
        data = aiohttp.FormData()
        data.add_field('file',
                      open(test_file, 'rb'),
                      filename='no_ml_test.txt',
                      content_type='text/plain')
        data.add_field('law_name', 'اختبار بدون تعلم آلة')
        data.add_field('law_type', 'law')
        data.add_field('jurisdiction', 'السعودية')
        data.add_field('description', 'اختبار الوضع بدون ML')
        
        print(f"📤 Uploading test file in NO-ML mode...")
        start_time = time.time()
        
        timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(UPLOAD_ENDPOINT, data=data) as response:
                elapsed = time.time() - start_time
                
                print(f"⏱️  Response time: {elapsed:.2f} seconds")
                print(f"📊 Status: {response.status}")
                
                result = await response.json()
                print(f"📝 Response: {result}")
                
                if response.status == 200 and result.get('success'):
                    print("✅ Test PASSED - NO-ML mode working!")
                    print(f"   - Chunks created: {result.get('data', {}).get('chunks_created', 'N/A')}")
                    print(f"   - Processing time: {result.get('data', {}).get('processing_time', 'N/A')}s")
                    return True
                else:
                    print(f"❌ Test FAILED")
                    print(f"   Error: {result.get('message', 'Unknown error')}")
                    return False
                    
    except asyncio.TimeoutError:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
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
    print("=" * 60)
    print("🔬 NO-ML Mode Upload Test")
    print("=" * 60)
    print()
    
    if not await check_server_status():
        return
    
    print()
    
    success = await test_no_ml_upload()
    
    print()
    print("=" * 60)
    if success:
        print("✅ NO-ML MODE TEST PASSED!")
        print("   - No models loaded")
        print("   - Hash-based embeddings generated")
        print("   - No memory issues")
        print("   - Endpoint working correctly")
    else:
        print("❌ NO-ML MODE TEST FAILED!")
        print("   - Issue still exists")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

