"""
Test script for the updated query endpoint that returns AI-generated answers.

This script tests the new behavior where the endpoint returns clear answers
instead of raw chunks.
"""

import requests
import json
import os
from typing import Dict, Any

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_ENDPOINT = f"{BASE_URL}/api/v1/legal/laws/query"

# Test queries in Arabic
TEST_QUERIES = [
    "ماهي مهام واختصاصات مفتشي العمل؟",
    "ما هي حقوق العامل في إجازة الحج؟",
    "كم المدة القانونية لإجازة الوضع للمرأة العاملة؟",
    "ما هي حقوق العامل عند إنهاء العقد؟",
    "ما هي واجبات صاحب العمل تجاه العمال؟"
]


def get_auth_token() -> str:
    """
    Get authentication token.
    You need to replace this with your actual authentication flow.
    """
    # Option 1: Read from environment variable
    token = os.getenv("API_AUTH_TOKEN")
    if token:
        return token
    
    # Option 2: Login to get token (implement your login logic here)
    # login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", ...)
    # return login_response.json()["data"]["access_token"]
    
    # Option 3: For testing, return None if no auth required
    print("⚠️  No auth token found. Set API_AUTH_TOKEN environment variable.")
    return None


def test_query(query: str, auth_token: str = None, top_k: int = 5) -> Dict[str, Any]:
    """
    Test a single query against the endpoint.
    """
    print(f"\n{'='*80}")
    print(f"🔍 Testing Query: {query}")
    print(f"{'='*80}")
    
    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # Prepare request
    payload = {
        "query": query,
        "top_k": top_k
    }
    
    try:
        # Make request
        print(f"📤 Sending request to: {API_ENDPOINT}")
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        # Parse response
        data = response.json()
        
        # Display results
        print(f"\n✅ Success: {data.get('success', False)}")
        print(f"📝 Message: {data.get('message', 'No message')}")
        
        if data.get('success'):
            answer = data.get('data', {}).get('answer', 'No answer provided')
            print(f"\n💡 AI-Generated Answer:")
            print(f"{'─'*80}")
            print(answer)
            print(f"{'─'*80}")
        else:
            print(f"\n❌ Error:")
            print(f"   {data.get('message', 'Unknown error')}")
            if 'errors' in data and data['errors']:
                for error in data['errors']:
                    print(f"   - {error}")
        
        return data
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>30 seconds)")
        return {"success": False, "error": "timeout"}
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {BASE_URL}")
        print("   Make sure your server is running!")
        return {"success": False, "error": "connection_error"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def compare_old_vs_new_format():
    """
    Show the difference between old and new response formats.
    """
    print("\n" + "="*80)
    print("📊 OLD vs NEW RESPONSE FORMAT")
    print("="*80)
    
    print("\n❌ OLD FORMAT (Raw Chunks):")
    print(json.dumps({
        "success": True,
        "message": "Found 5 relevant results",
        "data": {
            "chunks": [
                {
                    "content": "المادة 120: يصدر الوزير القواعد...",
                    "score": 1349.68,
                    "article_number": "120"
                }
            ]
        }
    }, ensure_ascii=False, indent=2))
    
    print("\n✅ NEW FORMAT (AI-Generated Answer):")
    print(json.dumps({
        "success": True,
        "message": "بناءً على المادة 138...",
        "data": {
            "answer": "بناءً على المادة 138 من نظام العمل السعودي، تشمل مهام مفتشي العمل...",
            "query": "ماهي مهام واختصاصات مفتشي العمل؟"
        }
    }, ensure_ascii=False, indent=2))


def run_all_tests():
    """
    Run all test queries.
    """
    print("\n" + "🎯"*40)
    print("TESTING UPDATED QUERY ENDPOINT - AI-GENERATED ANSWERS")
    print("🎯"*40)
    
    # Get auth token
    auth_token = get_auth_token()
    
    # Show format comparison
    compare_old_vs_new_format()
    
    # Run tests
    results = []
    for query in TEST_QUERIES:
        result = test_query(query, auth_token)
        results.append({
            "query": query,
            "success": result.get("success", False),
            "has_answer": bool(result.get("data", {}).get("answer"))
        })
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r["success"])
    with_answers = sum(1 for r in results if r["has_answer"])
    
    print(f"\nTotal Queries: {len(results)}")
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"💡 With AI Answers: {with_answers}/{len(results)}")
    
    if successful == len(results) and with_answers == len(results):
        print("\n🎉 ALL TESTS PASSED! The endpoint is working correctly.")
    elif successful > 0:
        print("\n⚠️  PARTIAL SUCCESS. Some queries worked, others failed.")
        print("   Check the error messages above.")
    else:
        print("\n❌ ALL TESTS FAILED.")
        print("   Common issues:")
        print("   1. Server not running")
        print("   2. Authentication token missing/invalid")
        print("   3. Gemini API key not configured")
        print("   4. No documents uploaded")
    
    print("\n" + "="*80)


def test_single_query_interactive():
    """
    Interactive mode to test a single query.
    """
    print("\n🔍 INTERACTIVE QUERY TESTING")
    print("="*80)
    
    # Get auth token
    auth_token = get_auth_token()
    
    # Get query from user
    print("\nEnter your question in Arabic:")
    query = input("❓ ")
    
    if not query.strip():
        print("❌ Empty query. Exiting.")
        return
    
    # Test the query
    test_query(query, auth_token)


if __name__ == "__main__":
    import sys
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   QUERY ENDPOINT TEST SUITE                                  ║
║                   Testing AI-Generated Answers                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Interactive mode
        test_single_query_interactive()
    else:
        # Run all tests
        print("💡 Tip: Use --interactive flag for interactive testing")
        print("   Example: python test_query_endpoint.py --interactive\n")
        run_all_tests()
    
    print("\n✅ Testing complete!")
    print("\n📝 Notes:")
    print("   - Make sure your server is running (python run.py)")
    print("   - Set API_AUTH_TOKEN environment variable if auth is required")
    print("   - Ensure GEMINI_API_KEY is configured in your .env file")
    print("   - Documents must be uploaded and indexed first")

