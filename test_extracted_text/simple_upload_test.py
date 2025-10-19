"""
Simple upload test without ML embeddings to verify basic functionality.

This test uploads a document but skips embedding generation to isolate the issue.
"""

import asyncio
import aiohttp
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/rag/upload-document"

# Very simple test content
SIMPLE_CONTENT = """
اختبار بسيط

المادة 1: نص قصير.
المادة 2: اختبار آخر.
"""


async def create_simple_test_file():
    """Create a simple test file"""
    test_file = Path("simple_test.txt")
    test_file.write_text(SIMPLE_CONTENT, encoding='utf-8')
    return test_file


async def test_basic_upload():
    """Test basic upload without embeddings"""
    print("🧪 Testing basic upload (no embeddings)...")
    
    test_file = await create_simple_test_file()
    
    try:
        data = aiohttp.FormData()
        data.add_field('file',
                      open(test_file, 'rb'),
                      filename='simple_test.txt',
                      content_type='text/plain')
        data.add_field('law_name', 'اختبار بسيط')
        data.add_field('law_type', 'law')
        data.add_field('jurisdiction', 'السعودية')
        
        print(f"📤 Uploading simple test file...")
        start_time = time.time()
        
        timeout = aiohttp.ClientTimeout(total=30)  # 30 seconds
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(UPLOAD_ENDPOINT, data=data) as response:
                elapsed = time.time() - start_time
                
                print(f"⏱️  Response time: {elapsed:.2f} seconds")
                print(f"📊 Status: {response.status}")
                
                result = await response.json()
                print(f"📝 Response: {result}")
                
                if response.status == 200:
                    print("✅ Basic upload works!")
                    return True
                else:
                    print("❌ Basic upload failed")
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


async def main():
    print("=" * 50)
    print("🔬 Simple Upload Test (No Embeddings)")
    print("=" * 50)
    
    success = await test_basic_upload()
    
    print("=" * 50)
    if success:
        print("✅ Basic functionality works!")
        print("   The issue is likely with ML model loading.")
    else:
        print("❌ Basic functionality also fails!")
        print("   There's a deeper issue with the endpoint.")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

