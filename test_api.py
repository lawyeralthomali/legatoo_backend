#!/usr/bin/env python3
"""Simple API test script to check CORS and connectivity."""

import requests
import json
import sys

def test_api():
    """Test the API endpoints."""
    base_url = "http://127.0.0.1:8000"
    
    endpoints = [
        "/cors-test",
        "/health", 
        "/",
        "/api/v1/auth/login"
    ]
    
    print("Testing API endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            print(f"\nTesting: {url}")
            response = requests.get(url, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"Response (text): {response.text[:200]}...")
            else:
                print(f"Error Response: {response.text}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("API Test Complete")

if __name__ == "__main__":
    test_api()

