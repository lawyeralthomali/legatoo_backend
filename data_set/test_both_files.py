#!/usr/bin/env python3
"""
Test Both JSON Files

This script tests both JSON files in the data_set/files directory.
"""

import requests
import json
import os

def test_json_file(base_url: str, json_file_path: str, auth_token: str):
    """Test uploading a single JSON file."""
    
    print(f"📤 Testing: {json_file_path}")
    
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
                print(f"✅ Success: {stats['total_branches']} branches, {stats['total_chapters']} chapters, {stats['total_articles']} articles")
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

def main():
    """Main function to test both files."""
    print("=" * 60)
    print("🧪 TESTING BOTH JSON FILES")
    print("=" * 60)
    
    # Configuration
    base_url = "http://127.0.0.1:8000"
    files_to_test = [
        "files/1.json",
        "files/extracted_legal_structure.json"
    ]
    
    # Get authentication token
    email = input("Enter your email: ").strip()
    password = input("Enter your password: ").strip()
    
    if not email or not password:
        print("❌ Email and password are required")
        return
    
    # Authenticate
    print("🔐 Authenticating...")
    login_data = {"email": email, "password": password}
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Authentication failed: HTTP {response.status_code}")
            return
        
        data = response.json()
        if not data.get("success"):
            print(f"❌ Authentication failed: {data.get('message')}")
            return
        
        auth_token = data["data"]["access_token"]
        print("✅ Authentication successful")
        
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return
    
    # Test each file
    results = []
    for file_path in files_to_test:
        if os.path.exists(file_path):
            success = test_json_file(base_url, file_path, auth_token)
            results.append({"file": file_path, "success": success})
        else:
            print(f"⚠️ File not found: {file_path}")
            results.append({"file": file_path, "success": False})
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total}")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['file']}")
    
    if successful == total:
        print("\n🎉 All tests completed successfully!")
    else:
        print(f"\n⚠️ {total - successful} tests failed")

if __name__ == "__main__":
    main()
