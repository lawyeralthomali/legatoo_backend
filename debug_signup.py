#!/usr/bin/env python3
"""
Debug signup endpoint to identify the issue
"""
import requests
import json

def test_signup():
    """Test the signup endpoint with debugging"""
    print("🧪 Testing Signup Endpoint")
    print("=" * 50)
    
    # Test data with Saudi phone number
    test_data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "0501234567"
    }
    
    print(f"📤 Sending request to: http://localhost:8000/api/v1/supabase-auth/signup")
    print(f"📋 Request data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/supabase-auth/signup",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📋 Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"📋 Response Text: {response.text}")
            
        if response.status_code == 200:
            print("\n✅ Signup successful!")
        else:
            print(f"\n❌ Signup failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running on localhost:8000?")
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_signup()
