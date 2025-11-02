"""
Test the actual API endpoint to verify the fix is working.
This simulates what the frontend would do.
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"
SEARCH_ENDPOINT = f"{BASE_URL}/api/v1/search/similar-laws"

def test_search_endpoint():
    """Test the search endpoint with various queries."""
    print("=" * 80)
    print("TESTING API ENDPOINT: /api/v1/search/similar-laws")
    print("=" * 80)
    
    test_cases = [
        {
            "query": "حقوق العامل",
            "top_k": 5,
            "threshold": 0.4
        },
        {
            "query": "إنهاء عقد العمل",
            "top_k": 5,
            "threshold": 0.4
        },
        {
            "query": "الإجازات السنوية",
            "top_k": 5,
            "threshold": 0.3
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}")
        print(f"{'='*80}")
        print(f"Query: {test_case['query']}")
        print(f"Top K: {test_case['top_k']}")
        print(f"Threshold: {test_case['threshold']}")
        print("-" * 80)
        
        try:
            response = requests.post(
                SEARCH_ENDPOINT,
                json=test_case,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print(f"✅ Success: {data.get('message')}")
                    results = data.get("data", {}).get("results", [])
                    print(f"Total Results: {len(results)}")
                    
                    for j, result in enumerate(results[:3], 1):
                        print(f"\n  Result {j}:")
                        print(f"    Similarity: {result['similarity']:.4f}")
                        print(f"    Content: {result['content'][:100]}...")
                        if 'law_metadata' in result:
                            print(f"    Law: {result['law_metadata'].get('law_name', 'N/A')}")
                else:
                    print(f"❌ Failed: {data.get('message')}")
            else:
                print(f"❌ HTTP Error {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Is the server running?")
            print(f"   Start server with: python start_server.py or uvicorn app.main:app --reload")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")
    print("\n📝 Note: To test this, start the server first:")
    print("   python start_server.py")
    print("   or")
    print("   uvicorn app.main:app --reload")


if __name__ == "__main__":
    test_search_endpoint()

