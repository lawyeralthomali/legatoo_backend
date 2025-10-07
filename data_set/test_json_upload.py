#!/usr/bin/env python3
"""
Test JSON Upload Script

This script tests the JSON upload endpoint with the extracted_legal_structure.json file.
"""

import requests
import json
import os

def test_json_upload():
    """Test the JSON upload endpoint."""
    
    # Configuration
    base_url = "http://127.0.0.1:8000"
    json_file_path = "files/extracted_legal_structure.json"
    
    print("🧪 Testing JSON Upload Endpoint")
    print("=" * 50)
    
    # Check if JSON file exists
    if not os.path.exists(json_file_path):
        print(f"❌ JSON file not found: {json_file_path}")
        return False
    
    # Get authentication token (you'll need to provide valid credentials)
    email = input("Enter your email: ").strip()
    password = input("Enter your password: ").strip()
    
    if not email or not password:
        print("❌ Email and password are required")
        return False
    
    # Authenticate
    print("🔐 Authenticating...")
    login_data = {"email": email, "password": password}
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Authentication failed: HTTP {response.status_code}")
            return False
        
        data = response.json()
        if not data.get("success"):
            print(f"❌ Authentication failed: {data.get('message')}")
            return False
        
        auth_token = data["data"]["access_token"]
        print("✅ Authentication successful")
        
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return False
    
    # Upload JSON file
    print("📤 Uploading JSON file...")
    
    try:
        with open(json_file_path, 'rb') as f:
            files = {
                'json_file': (os.path.basename(json_file_path), f, 'application/json')
            }
            
            headers = {
                "Authorization": f"Bearer {auth_token}"
            }
            
            response = requests.post(
                f"{base_url}/api/v1/laws/upload-json",
                files=files,
                headers=headers
            )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stats = data["data"]["statistics"]
                print("✅ Upload successful!")
                print(f"📊 Statistics:")
                print(f"   - Branches: {stats['total_branches']}")
                print(f"   - Chapters: {stats['total_chapters']}")
                print(f"   - Articles: {stats['total_articles']}")
                print(f"   - Law Source: {data['data']['law_source']['name']}")
                return True
            else:
                print(f"❌ Upload failed: {data.get('message')}")
                return False
        else:
            print(f"❌ Upload failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_json_upload()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed!")
