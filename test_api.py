#!/usr/bin/env python3
"""
Test script for Supabase Auth FastAPI endpoints
"""

import requests
import json

# Configuration
API_BASE = "http://localhost:8000"
JWT_TOKEN = "YOUR_SUPABASE_JWT_TOKEN_HERE"  # Replace with actual token

def test_api_endpoints():
    """Test the FastAPI endpoints with authentication."""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Supabase Auth FastAPI Endpoints")
    print("=" * 50)
    
    # Test 1: Get current user info
    print("\n1️⃣ Testing GET /api/v1/users/me")
    try:
        response = requests.get(f"{API_BASE}/api/v1/users/me", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ User info: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: Get auth status
    print("\n2️⃣ Testing GET /api/v1/users/me/auth-status")
    try:
        response = requests.get(f"{API_BASE}/api/v1/users/me/auth-status", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Auth status: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 3: Get profile (will create if not exists)
    print("\n3️⃣ Testing GET /api/v1/profiles/me")
    try:
        response = requests.get(f"{API_BASE}/api/v1/profiles/me", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Profile: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 4: Update profile
    print("\n4️⃣ Testing PUT /api/v1/profiles/me")
    profile_update = {
        "full_name": "John Doe",
        "bio": "Software Developer",
        "avatar_url": "https://example.com/avatar.jpg"
    }
    try:
        response = requests.put(f"{API_BASE}/api/v1/profiles/me", 
                              headers=headers, 
                              json=profile_update)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Updated profile: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 5: Create profile explicitly
    print("\n5️⃣ Testing POST /api/v1/profiles/")
    profile_create = {
        "full_name": "Jane Smith",
        "bio": "Product Manager",
        "avatar_url": None
    }
    try:
        response = requests.post(f"{API_BASE}/api/v1/profiles/", 
                               headers=headers, 
                               json=profile_create)
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            print(f"✅ Created profile: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_without_auth():
    """Test endpoints without authentication (should fail)."""
    
    print("\n🔒 Testing without authentication (should fail)")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE}/api/v1/users/me")
        print(f"GET /api/v1/users/me without auth: {response.status_code}")
        if response.status_code == 401:
            print("✅ Correctly rejected unauthorized request")
        else:
            print(f"❌ Unexpected response: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🚀 Supabase Auth FastAPI Test Script")
    print("=" * 50)
    print("📋 Instructions:")
    print("1. Make sure your FastAPI app is running on http://localhost:8000")
    print("2. Get a JWT token from Supabase Auth")
    print("3. Replace JWT_TOKEN variable with your actual token")
    print("4. Run this script: python test_api.py")
    print()
    
    if JWT_TOKEN == "YOUR_SUPABASE_JWT_TOKEN_HERE":
        print("❌ Please set your JWT token in the JWT_TOKEN variable!")
        print("\n🔑 How to get JWT token:")
        print("1. Go to Supabase Dashboard → Authentication → Users")
        print("2. Create a user or use existing user")
        print("3. Use Supabase client to get session token")
        print("4. Copy the access_token from the session")
        exit(1)
    
    test_api_endpoints()
    test_without_auth()
    
    print("\n✅ Testing complete!")

