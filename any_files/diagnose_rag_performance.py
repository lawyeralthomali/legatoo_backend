#!/usr/bin/env python3
"""
RAG System Performance Diagnostic Script

This script helps identify why the RAG system might be taking a long time
by testing each component individually and measuring performance.
"""

import asyncio
import time
import json
import tempfile
import os
from pathlib import Path

# Mock FastAPI UploadFile for testing
class MockUploadFile:
    def __init__(self, content: bytes, filename: str):
        self.content = content
        self.filename = filename
        self._position = 0
    
    async def read(self, size: int = -1) -> bytes:
        if size == -1:
            result = self.content[self._position:]
            self._position = len(self.content)
        else:
            result = self.content[self._position:self._position + size]
            self._position += len(result)
        return result

def create_test_document(num_articles: int = 50) -> dict:
    """Create a small test document for quick testing."""
    articles = []
    
    for i in range(num_articles):
        article = {
            "article": f"المادة {i+1}",
            "text": f"هذا نص المادة {i+1} من القانون التجاري السعودي. تحتوي هذه المادة على أحكام مهمة تتعلق بالتجارة والاستثمار في المملكة العربية السعودية.",
            "keywords": [f"تجارة", f"استثمار", f"قانون"],
            "order_index": i
        }
        articles.append(article)
    
    return {
        "law_sources": {
            "name": "القانون التجاري السعودي",
            "type": "قانون تجاري",
            "jurisdiction": "المملكة العربية السعودية",
            "issuing_authority": "وزارة التجارة والاستثمار",
            "issue_date": "2023-01-01",
            "articles": articles
        }
    }

async def test_model_initialization():
    """Test model initialization performance."""
    print("🔧 Testing Model Initialization...")
    print("-" * 40)
    
    start_time = time.time()
    
    try:
        from app.services.knowledge.optimized_knowledge_service import model_manager
        
        init_time = time.time() - start_time
        print(f"✅ Models initialized in: {init_time:.2f} seconds")
        
        # Test individual components
        print(f"📊 Embedding model: {model_manager.embeddings}")
        print(f"📊 Reranker model: {model_manager.reranker_model}")
        print(f"📊 Text splitter: {model_manager.text_splitter}")
        print(f"📊 Gemini client: {model_manager.gemini_client}")
        
        return True, init_time
        
    except Exception as e:
        error_time = time.time() - start_time
        print(f"❌ Model initialization failed: {e}")
        print(f"⏱️ Failed after: {error_time:.2f} seconds")
        return False, error_time

async def test_vectorstore_connection():
    """Test vectorstore connection performance."""
    print("\n🗄️ Testing Vectorstore Connection...")
    print("-" * 40)
    
    start_time = time.time()
    
    try:
        from app.services.knowledge.optimized_knowledge_service import model_manager
        
        vectorstore = model_manager.get_vectorstore()
        collection = vectorstore._collection
        
        conn_time = time.time() - start_time
        print(f"✅ Vectorstore connected in: {conn_time:.2f} seconds")
        
        # Get document count
        doc_count = collection.count() if collection else 0
        print(f"📊 Total documents in vectorstore: {doc_count}")
        
        return True, conn_time, doc_count
        
    except Exception as e:
        error_time = time.time() - start_time
        print(f"❌ Vectorstore connection failed: {e}")
        print(f"⏱️ Failed after: {error_time:.2f} seconds")
        return False, error_time, 0

async def test_file_processing():
    """Test file processing performance."""
    print("\n📁 Testing File Processing...")
    print("-" * 40)
    
    # Create small test document
    test_doc = create_test_document(20)  # Small test with 20 articles
    json_content = json.dumps(test_doc, ensure_ascii=False, indent=2)
    json_bytes = json_content.encode('utf-8')
    
    print(f"📊 Test document: {len(json_bytes) / 1024:.1f} KB, {len(test_doc['law_sources']['articles'])} articles")
    
    mock_file = MockUploadFile(json_bytes, "test_small.json")
    
    start_time = time.time()
    
    try:
        from app.services.knowledge.optimized_knowledge_service import process_upload_optimized
        
        chunks_count = await process_upload_optimized(mock_file)
        
        process_time = time.time() - start_time
        print(f"✅ File processed in: {process_time:.2f} seconds")
        print(f"📊 Chunks created: {chunks_count}")
        print(f"📈 Processing rate: {len(test_doc['law_sources']['articles']) / process_time:.1f} articles/second")
        
        return True, process_time, chunks_count
        
    except Exception as e:
        error_time = time.time() - start_time
        print(f"❌ File processing failed: {e}")
        print(f"⏱️ Failed after: {error_time:.2f} seconds")
        import traceback
        traceback.print_exc()
        return False, error_time, 0

async def test_query_processing():
    """Test query processing performance."""
    print("\n🔍 Testing Query Processing...")
    print("-" * 40)
    
    test_queries = [
        "ما هي أحكام القانون التجاري؟",
        "ما هي عقوبات التهرب الضريبي؟",
        "ما هي حقوق المستثمرين؟"
    ]
    
    try:
        from app.services.knowledge.optimized_knowledge_service import answer_query
        
        for i, query in enumerate(test_queries, 1):
            print(f"🔍 Test query {i}: {query}")
            
            start_time = time.time()
            result = await answer_query(query)
            query_time = time.time() - start_time
            
            if isinstance(result, dict):
                answer = result.get("answer", "No answer")
                context_count = len(result.get("retrieved_context", []))
            else:
                answer = str(result)
                context_count = 0
            
            print(f"✅ Query {i} processed in: {query_time:.2f} seconds")
            print(f"📊 Retrieved context: {context_count} articles")
            print(f"📝 Answer preview: {answer[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Query processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_system_resources():
    """Test system resource usage."""
    print("\n💻 Testing System Resources...")
    print("-" * 40)
    
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"📊 CPU usage: {cpu_percent}%")
        
        # Memory usage
        memory = psutil.virtual_memory()
        print(f"📊 Memory usage: {memory.percent}% ({memory.used / 1024 / 1024 / 1024:.1f} GB used)")
        
        # Disk usage
        disk = psutil.disk_usage('.')
        print(f"📊 Disk usage: {disk.percent}% ({disk.free / 1024 / 1024 / 1024:.1f} GB free)")
        
        return True
        
    except ImportError:
        print("⚠️ psutil not available - install with: pip install psutil")
        return False
    except Exception as e:
        print(f"❌ Resource monitoring failed: {e}")
        return False

async def main():
    """Main diagnostic function."""
    print("🔍 RAG System Performance Diagnostic")
    print("=" * 50)
    
    total_start = time.time()
    results = {}
    
    # Test 1: Model Initialization
    success, time_taken = await test_model_initialization()
    results['model_init'] = {'success': success, 'time': time_taken}
    
    if not success:
        print("\n❌ Model initialization failed - this is likely the main issue!")
        print("💡 Possible solutions:")
        print("   - Check GEMINI_API_KEY environment variable")
        print("   - Ensure internet connection for model downloads")
        print("   - Check available disk space")
        return
    
    # Test 2: Vectorstore Connection
    success, time_taken, doc_count = await test_vectorstore_connection()
    results['vectorstore'] = {'success': success, 'time': time_taken, 'doc_count': doc_count}
    
    # Test 3: File Processing
    success, time_taken, chunks = await test_file_processing()
    results['file_processing'] = {'success': success, 'time': time_taken, 'chunks': chunks}
    
    # Test 4: Query Processing
    success = await test_query_processing()
    results['query_processing'] = {'success': success}
    
    # Test 5: System Resources
    success = await test_system_resources()
    results['resources'] = {'success': success}
    
    # Summary
    total_time = time.time() - total_start
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"⏱️ Total diagnostic time: {total_time:.2f} seconds")
    print()
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
        
        if 'time' in result:
            print(f"   Time: {result['time']:.2f}s")
        if 'doc_count' in result:
            print(f"   Documents: {result['doc_count']}")
        if 'chunks' in result:
            print(f"   Chunks: {result['chunks']}")
    
    print("\n💡 PERFORMANCE RECOMMENDATIONS:")
    
    if results['model_init']['time'] > 10:
        print("   ⚠️ Model initialization is slow - consider caching models")
    
    if results['file_processing']['time'] > 5:
        print("   ⚠️ File processing is slow - check batch size settings")
    
    if results['query_processing']['success']:
        print("   ✅ Query processing is working correctly")
    else:
        print("   ❌ Query processing failed - check vectorstore and models")
    
    if results['vectorstore']['doc_count'] == 0:
        print("   ⚠️ No documents in vectorstore - upload some files first")
    
    print("\n🎯 NEXT STEPS:")
    print("   1. If models failed to initialize, check environment variables")
    print("   2. If file processing is slow, try smaller batch sizes")
    print("   3. If queries fail, ensure documents are uploaded first")
    print("   4. Check system resources if performance is poor")

if __name__ == "__main__":
    asyncio.run(main())
