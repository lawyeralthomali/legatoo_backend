"""
Final simplified test - query existing data
"""
import requests

BASE_URL = "http://192.168.100.13:8000"

print("=" * 70)
print("FINAL TEST: Login -> Query")
print("=" * 70)

# Step 1: Login
print("\n📝 Step 1: Logging in...")
try:
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "legatoo@althomalilawfirm.sa",
        "password": "Zaq1zaq1"
    }, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        exit(1)
    
    token = response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in")
except Exception as e:
    print(f"❌ Login error: {e}")
    print("\n⚠️ The server may not be running or is not responding.")
    exit(1)

# Step 2: Query
print("\n🔍 Step 2: Querying...")
query = "المادة الاولى"
query_params = {"query": query, "top_k": 3}

try:
    response = requests.post(
        f"{BASE_URL}/api/v1/laws/query",
        headers=headers,
        params=query_params,
        timeout=15
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:300]}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Query successful!")
        if result.get('success'):
            data = result.get('data', {})
            print(f"Results: {data.get('results_count', 0)}")
    
except Exception as e:
    print(f"\n❌ Query error: {e}")

print("\n" + "=" * 70)
