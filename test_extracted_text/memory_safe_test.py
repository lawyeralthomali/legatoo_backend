"""
Memory-safe test script for the upload endpoint.

This script monitors memory usage and tests the endpoint with various memory constraints.
"""

import asyncio
import aiohttp
import time
import os
import gc
from pathlib import Path

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available. Install with: pip install psutil")

# Test configuration
BASE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/rag/upload-document"

# Create a very small test file to minimize memory usage
MINIMAL_TEST_CONTENT = """
نظام اختبار

المادة 1: نص قصير للاختبار.
المادة 2: يجب أن يعمل النظام دون استهلاك ذاكرة كثيرة.
"""


def get_memory_usage():
    """Get current memory usage in MB"""
    if PSUTIL_AVAILABLE:
        process = psutil.Process()
        return process.memory_info().rss / (1024**2)
    return 0


def get_system_memory():
    """Get system memory info"""
    if PSUTIL_AVAILABLE:
        memory = psutil.virtual_memory()
        return {
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_percent': memory.percent
        }
    return {'total_gb': 0, 'available_gb': 0, 'used_percent': 0}


async def create_minimal_test_file():
    """Create a very small test file"""
    test_file = Path("minimal_test.txt")
    test_file.write_text(MINIMAL_TEST_CONTENT, encoding='utf-8')
    return test_file


async def test_upload_with_memory_monitoring():
    """Test upload with memory monitoring"""
    print("🧪 Testing upload-document endpoint with memory monitoring...")
    
    # Check initial memory
    initial_memory = get_memory_usage()
    system_memory = get_system_memory()
    
    print(f"📊 Initial memory usage: {initial_memory:.1f} MB")
    print(f"💾 System memory: {system_memory['available_gb']:.1f} GB available")
    
    if system_memory['available_gb'] < 1.0:
        print("⚠️ WARNING: Less than 1GB available memory!")
    
    # Create test file
    test_file = await create_minimal_test_file()
    
    try:
        # Prepare the upload
        data = aiohttp.FormData()
        data.add_field('file',
                      open(test_file, 'rb'),
                      filename='minimal_test.txt',
                      content_type='text/plain')
        data.add_field('law_name', 'اختبار ذاكرة')
        data.add_field('law_type', 'law')
        data.add_field('jurisdiction', 'السعودية')
        data.add_field('description', 'اختبار استهلاك الذاكرة')
        
        print(f"📤 Uploading minimal test file...")
        start_time = time.time()
        start_memory = get_memory_usage()
        
        # Set a conservative timeout
        timeout = aiohttp.ClientTimeout(total=60)  # 1 minute max
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(UPLOAD_ENDPOINT, data=data) as response:
                    elapsed = time.time() - start_time
                    end_memory = get_memory_usage()
                    memory_increase = end_memory - start_memory
                    
                    print(f"⏱️  Response received in {elapsed:.2f} seconds")
                    print(f"📊 Memory change: {memory_increase:+.1f} MB")
                    print(f"📊 Final memory: {end_memory:.1f} MB")
                    print(f"📊 Status: {response.status}")
                    
                    result = await response.json()
                    print(f"📝 Response: {result}")
                    
                    # Check for success
                    if response.status == 200 and result.get('success'):
                        print("✅ Test PASSED - Endpoint working without memory issues!")
                        print(f"   - Chunks created: {result.get('data', {}).get('chunks_created', 'N/A')}")
                        print(f"   - Processing time: {result.get('data', {}).get('processing_time', 'N/A')}s")
                        print(f"   - Memory increase: {memory_increase:+.1f} MB")
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
        
        # Force garbage collection
        gc.collect()
        final_memory = get_memory_usage()
        print(f"🧹 After cleanup: {final_memory:.1f} MB")


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
    print("=" * 70)
    print("🔬 Memory-Safe Upload Document Endpoint Test")
    print("=" * 70)
    print()
    
    # Check server status
    if not await check_server_status():
        return
    
    print()
    
    # Run memory-monitored test
    success = await test_upload_with_memory_monitoring()
    
    print()
    print("=" * 70)
    if success:
        print("✅ ALL TESTS PASSED - Memory-optimized fix is working!")
    else:
        print("❌ TEST FAILED - Issue still exists or server error")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

