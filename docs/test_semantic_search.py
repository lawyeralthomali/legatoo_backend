"""
Test Semantic Search System
اختبار شامل لنظام البحث الدلالي

Usage:
    python test_semantic_search.py

Requirements:
    - Server running on http://localhost:8000
    - Valid JWT token
    - Embeddings generated for chunks
"""

import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None  # سيتم طلبه من المستخدم

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """طباعة رأس ملون"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """طباعة رسالة نجاح"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text: str):
    """طباعة رسالة خطأ"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text: str):
    """طباعة معلومات"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def get_auth_headers() -> dict:
    """الحصول على headers المصادقة"""
    return {"Authorization": f"Bearer {TOKEN}"}


def test_server_connection():
    """اختبار اتصال السيرفر"""
    print_header("🔌 Testing Server Connection")
    
    try:
        response = requests.get(f"{BASE_URL.rsplit('/api', 1)[0]}/")
        if response.status_code == 200:
            print_success("Server is running!")
            return True
        else:
            print_error(f"Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Make sure it's running on http://localhost:8000")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_statistics():
    """اختبار endpoint الإحصائيات"""
    print_header("📊 Testing Search Statistics")
    
    try:
        response = requests.get(
            f"{BASE_URL}/search/statistics",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data['data']
                print_success("Statistics retrieved successfully!")
                print_info(f"Total Searchable Chunks: {stats.get('total_searchable_chunks', 0)}")
                print_info(f"Law Chunks: {stats.get('law_chunks', 0)}")
                print_info(f"Case Chunks: {stats.get('case_chunks', 0)}")
                print_info(f"Cache Enabled: {stats.get('cache_enabled', False)}")
                return True
            else:
                print_error(f"API Error: {data.get('message', 'Unknown error')}")
                return False
        else:
            print_error(f"HTTP Error: {response.status_code}")
            if response.status_code == 401:
                print_error("Authentication failed. Check your token.")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_similar_laws():
    """اختبار البحث في القوانين"""
    print_header("📜 Testing Similar Laws Search")
    
    test_queries = [
        "فسخ عقد العمل",
        "الإجازات السنوية",
        "حقوق العامل"
    ]
    
    for query in test_queries:
        print_info(f"Query: '{query}'")
        
        try:
            response = requests.post(
                f"{BASE_URL}/search/similar-laws",
                params={
                    "query": query,
                    "top_k": 3,
                    "threshold": 0.7
                },
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    total = data['data'].get('total_results', 0)
                    print_success(f"Found {total} similar laws")
                    
                    for i, result in enumerate(data['data'].get('results', [])[:2], 1):
                        similarity = result.get('similarity', 0)
                        content = result.get('content', '')[:100]
                        print(f"   {i}. Similarity: {similarity:.2f} - {content}...")
                else:
                    print_error(f"API Error: {data.get('message')}")
            else:
                print_error(f"HTTP Error: {response.status_code}")
                
        except Exception as e:
            print_error(f"Exception: {str(e)}")
        
        print()  # Empty line between queries
    
    return True


def test_similar_cases():
    """اختبار البحث في القضايا"""
    print_header("⚖️ Testing Similar Cases Search")
    
    test_queries = [
        ("إنهاء خدمات عامل", "عمل"),
        ("تعويض عن فصل تعسفي", None),
        ("نزاع عمالي", "عمل")
    ]
    
    for query, case_type in test_queries:
        print_info(f"Query: '{query}'" + (f" (Type: {case_type})" if case_type else ""))
        
        try:
            params = {
                "query": query,
                "top_k": 3,
                "threshold": 0.7
            }
            if case_type:
                params['case_type'] = case_type
            
            response = requests.post(
                f"{BASE_URL}/search/similar-cases",
                params=params,
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    total = data['data'].get('total_results', 0)
                    print_success(f"Found {total} similar cases")
                    
                    for i, result in enumerate(data['data'].get('results', [])[:2], 1):
                        similarity = result.get('similarity', 0)
                        content = result.get('content', '')[:100]
                        print(f"   {i}. Similarity: {similarity:.2f} - {content}...")
                else:
                    print_error(f"API Error: {data.get('message')}")
            else:
                print_error(f"HTTP Error: {response.status_code}")
                
        except Exception as e:
            print_error(f"Exception: {str(e)}")
        
        print()
    
    return True


def test_hybrid_search():
    """اختبار البحث الهجين"""
    print_header("🔄 Testing Hybrid Search")
    
    query = "حقوق العامل في الإجازات"
    print_info(f"Query: '{query}'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/search/hybrid",
            params={
                "query": query,
                "search_types": "laws,cases",
                "top_k": 2,
                "threshold": 0.6
            },
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result_data = data['data']
                total = result_data.get('total_results', 0)
                print_success(f"Found {total} total results")
                
                if 'laws' in result_data:
                    law_count = result_data['laws'].get('count', 0)
                    print_info(f"📜 Laws: {law_count}")
                
                if 'cases' in result_data:
                    case_count = result_data['cases'].get('count', 0)
                    print_info(f"⚖️ Cases: {case_count}")
                
                return True
            else:
                print_error(f"API Error: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_suggestions():
    """اختبار الاقتراحات"""
    print_header("💡 Testing Search Suggestions")
    
    test_queries = ["نظام ال", "قانون", "محكمة"]
    
    for query in test_queries:
        print_info(f"Partial Query: '{query}'")
        
        try:
            response = requests.get(
                f"{BASE_URL}/search/suggestions",
                params={
                    "partial_query": query,
                    "limit": 5
                },
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    suggestions = data['data'].get('suggestions', [])
                    count = len(suggestions)
                    print_success(f"Found {count} suggestions")
                    
                    for i, suggestion in enumerate(suggestions[:3], 1):
                        print(f"   {i}. {suggestion}")
                else:
                    print_error(f"API Error: {data.get('message')}")
            else:
                print_error(f"HTTP Error: {response.status_code}")
                
        except Exception as e:
            print_error(f"Exception: {str(e)}")
        
        print()
    
    return True


def test_cache_operations():
    """اختبار عمليات الـ cache"""
    print_header("💾 Testing Cache Operations")
    
    try:
        # Clear cache
        response = requests.post(
            f"{BASE_URL}/search/clear-cache",
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Cache cleared successfully")
                return True
            else:
                print_error(f"API Error: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print(f"\n{Colors.BOLD}{'🎯'*30}{Colors.ENDC}")
    print(f"{Colors.BOLD}🚀 Semantic Search System - Complete Test Suite{Colors.ENDC}")
    print(f"{Colors.BOLD}{'🎯'*30}{Colors.ENDC}\n")
    
    # Test server connection first
    if not test_server_connection():
        print_error("\n❌ Server connection failed. Stopping tests.")
        return
    
    # Get token if not set
    global TOKEN
    if not TOKEN:
        print_info("Please enter your JWT token:")
        TOKEN = input("> ").strip()
        if not TOKEN:
            print_error("Token is required!")
            return
    
    # Run all tests
    tests = [
        ("Statistics", test_statistics),
        ("Similar Laws", test_similar_laws),
        ("Similar Cases", test_similar_cases),
        ("Hybrid Search", test_hybrid_search),
        ("Suggestions", test_suggestions),
        ("Cache Operations", test_cache_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print_header("📊 Test Summary")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        if success:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 All tests passed! System is working perfectly!{Colors.ENDC}\n")
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️ Some tests failed. Please check the errors above.{Colors.ENDC}\n")


if __name__ == "__main__":
    run_all_tests()
