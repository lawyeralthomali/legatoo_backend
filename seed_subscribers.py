"""
Seed script to create test subscribers using signup endpoint.
This script creates multiple test users who will automatically get subscriptions.
"""
import requests
import json
from typing import List, Dict
import time

# Configuration
BASE_URL = "http://localhost:8000"  # Change if your backend runs on a different port
SIGNUP_ENDPOINT = f"{BASE_URL}/api/v1/auth/signup"

# Test user data
TEST_USERS = [
    {
        "email": "ahmed.mohammed@example.com",
        "password": "SecurePass123!",
        "first_name": "Ahmed",
        "last_name": "Mohammed",
        "phone_number": "0501234567"
    },
    {
        "email": "fatima.ali@example.com",
        "password": "SecurePass123!",
        "first_name": "Fatima",
        "last_name": "Ali",
        "phone_number": "0502345678"
    },
    {
        "email": "sara.ahmad@example.com",
        "password": "SecurePass123!",
        "first_name": "Sara",
        "last_name": "Ahmad",
        "phone_number": "0503456789"
    },
    {
        "email": "mohammed.hassan@example.com",
        "password": "SecurePass123!",
        "first_name": "Mohammed",
        "last_name": "Hassan",
        "phone_number": "0504567890"
    },
    {
        "email": "noor.ibrahim@example.com",
        "password": "SecurePass123!",
        "first_name": "Noor",
        "last_name": "Ibrahim",
        "phone_number": "0505678901"
    },
    {
        "email": "khalid.omar@example.com",
        "password": "SecurePass123!",
        "first_name": "Khalid",
        "last_name": "Omar",
        "phone_number": "0506789012"
    },
    {
        "email": "layla.youssef@example.com",
        "password": "SecurePass123!",
        "first_name": "Layla",
        "last_name": "Youssef",
        "phone_number": "0507890123"
    },
    {
        "email": "omar.abdullah@example.com",
        "password": "SecurePass123!",
        "first_name": "Omar",
        "last_name": "Abdullah",
        "phone_number": "0508901234"
    },
    {
        "email": "mariam.saeed@example.com",
        "password": "SecurePass123!",
        "first_name": "Mariam",
        "last_name": "Saeed",
        "phone_number": "0509012345"
    },
    {
        "email": "yousef.mahmoud@example.com",
        "password": "SecurePass123!",
        "first_name": "Yousef",
        "last_name": "Mahmoud",
        "phone_number": "0510123456"
    }
]


def create_subscriber(user_data: Dict) -> Dict:
    """Create a single subscriber via signup endpoint."""
    try:
        response = requests.post(
            SIGNUP_ENDPOINT,
            json=user_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ Successfully created: {user_data['email']}")
            return {"success": True, "email": user_data["email"], "data": response.json()}
        else:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', error_data.get('message', str(response.text)))
            except:
                error_msg = response.text[:100]
            
            print(f"❌ Failed to create {user_data['email']}: {error_msg}")
            return {"success": False, "email": user_data["email"], "error": error_msg}
    except requests.exceptions.ConnectionError:
        error_msg = f"Could not connect to {BASE_URL}. Is the server running?"
        print(f"❌ Connection error for {user_data['email']}: {error_msg}")
        return {"success": False, "email": user_data["email"], "error": error_msg}
    except Exception as e:
        print(f"❌ Error creating {user_data['email']}: {str(e)}")
        return {"success": False, "email": user_data["email"], "error": str(e)}


def seed_subscribers():
    """Seed multiple subscribers."""
    print("🚀 Starting subscriber seeding...")
    print(f"📡 Connecting to: {BASE_URL}")
    print("-" * 60)
    
    results = []
    for user_data in TEST_USERS:
        result = create_subscriber(user_data)
        results.append(result)
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    print("-" * 60)
    print("\n📊 Seeding Summary:")
    successful = sum(1 for r in results if r.get("success"))
    failed = len(results) - successful
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if failed > 0:
        print("\n❌ Failed users:")
        for r in results:
            if not r.get("success"):
                print(f"  - {r['email']}: {r.get('error', 'Unknown error')}")
    
    print("\n✨ Seeding complete!")
    print(f"💡 Note: Each user automatically gets a free plan subscription when they signup.")
    return results


if __name__ == "__main__":
    print("=" * 60)
    print("  Subscriber Seeding Script")
    print("=" * 60)
    print("\nThis script will create test users via the signup endpoint.")
    print("Each user will automatically receive a subscription.\n")
    
    # Check if BASE_URL should be changed
    import sys
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
        SIGNUP_ENDPOINT = f"{BASE_URL}/api/v1/auth/signup"
        print(f"Using custom URL: {BASE_URL}\n")
    
    seed_subscribers()

