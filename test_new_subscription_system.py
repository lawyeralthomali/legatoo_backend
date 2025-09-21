"""
Test script for the new enhanced subscription system
Run this after setting up the new database tables
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test user credentials
TEST_USER_EMAIL = "mohammed211920@gmail.com"
TEST_JWT_TOKEN = "YOUR_JWT_TOKEN_HERE"  # Replace with actual token

async def test_new_subscription_system():
    """Test the complete new subscription system"""
    
    if TEST_JWT_TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("❌ Please update TEST_JWT_TOKEN with a real JWT token from Supabase")
        print("   1. Go to Supabase Dashboard > Authentication > Users")
        print("   2. Find 'mohammed211920@gmail.com'")
        print("   3. Copy the JWT token")
        print("   4. Update TEST_JWT_TOKEN in this script")
        return
    
    headers = {
        "Authorization": f"Bearer {TEST_JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing New Enhanced Subscription System")
        print("=" * 60)
        
        # Test 1: Health check
        print("\n1. Testing health check...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print(f"✅ Health check: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test 2: Get available plans
        print("\n2. Testing available plans...")
        try:
            response = await client.get(f"{API_BASE}/subscriptions/plans")
            if response.status_code == 200:
                plans = response.json()
                print(f"✅ Available plans: {len(plans)} plans found")
                for plan in plans[:3]:  # Show first 3 plans
                    print(f"   - {plan['plan_name']}: {plan['price']} {plan['currency']} ({plan['plan_type']})")
            else:
                print(f"❌ Plans failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Plans error: {e}")
        
        # Test 3: Get subscription status
        print("\n3. Testing subscription status...")
        try:
            response = await client.get(f"{API_BASE}/subscriptions/status", headers=headers)
            if response.status_code == 200:
                status = response.json()
                print(f"✅ Subscription status: {json.dumps(status, indent=2)}")
            else:
                print(f"❌ Subscription status failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Subscription status error: {e}")
        
        # Test 4: Test feature usage
        print("\n4. Testing feature usage...")
        try:
            response = await client.get(f"{API_BASE}/subscriptions/features/file_upload", headers=headers)
            if response.status_code == 200:
                usage = response.json()
                print(f"✅ File upload usage: {json.dumps(usage, indent=2)}")
            else:
                print(f"❌ Feature usage failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Feature usage error: {e}")
        
        # Test 5: Test file upload feature
        print("\n5. Testing file upload feature...")
        try:
            response = await client.get(f"{API_BASE}/premium/file-upload", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ File upload: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ File upload failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ File upload error: {e}")
        
        # Test 6: Test AI chat feature
        print("\n6. Testing AI chat feature...")
        try:
            response = await client.get(f"{API_BASE}/premium/ai-chat?message=Hello%20AI", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ AI chat: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ AI chat failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ AI chat error: {e}")
        
        # Test 7: Test contract feature
        print("\n7. Testing contract feature...")
        try:
            response = await client.get(f"{API_BASE}/premium/contracts", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Contract: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Contract failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Contract error: {e}")
        
        # Test 8: Test report feature
        print("\n8. Testing report feature...")
        try:
            response = await client.get(f"{API_BASE}/premium/reports", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Report: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Report failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Report error: {e}")
        
        # Test 9: Test token usage
        print("\n9. Testing token usage...")
        try:
            response = await client.get(f"{API_BASE}/premium/tokens?amount=50", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Token usage: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Token usage failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Token usage error: {e}")
        
        # Test 10: Test multi-user feature
        print("\n10. Testing multi-user feature...")
        try:
            response = await client.get(f"{API_BASE}/premium/multi-user", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Multi-user: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Multi-user failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Multi-user error: {e}")
        
        # Test 11: Test feature limits
        print("\n11. Testing feature limits...")
        try:
            response = await client.get(f"{API_BASE}/premium/feature-limits", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Feature limits: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Feature limits failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Feature limits error: {e}")
        
        # Test 12: Test usage summary
        print("\n12. Testing usage summary...")
        try:
            response = await client.get(f"{API_BASE}/premium/usage-summary", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Usage summary: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Usage summary failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Usage summary error: {e}")
        
        # Test 13: Test paid features (may fail if user has free plan)
        print("\n13. Testing paid features...")
        try:
            response = await client.get(f"{API_BASE}/premium/paid-features", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Paid features: {json.dumps(result, indent=2)}")
            else:
                print(f"⚠️  Paid features response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Paid features error: {e}")
        
        # Test 14: Test enterprise features (may fail if user doesn't have enterprise plan)
        print("\n14. Testing enterprise features...")
        try:
            response = await client.get(f"{API_BASE}/premium/enterprise-features", headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Enterprise features: {json.dumps(result, indent=2)}")
            else:
                print(f"⚠️  Enterprise features response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Enterprise features error: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 New subscription system test completed!")

def print_setup_instructions():
    """Print setup instructions for the new system"""
    
    print("📋 New Enhanced Subscription System Setup Instructions")
    print("=" * 60)
    
    print("\n🔧 Step 1: Database Setup")
    print("   1. Run 'database_setup_new.sql' in Supabase SQL Editor")
    print("   2. This creates the new tables: plans, subscriptions, usage_tracking, billing")
    print("   3. Inserts default plans and sets up triggers")
    
    print("\n🔄 Step 2: Migration (Optional)")
    print("   1. Run 'migrate_to_new_subscription_system.sql' to migrate existing data")
    print("   2. This migrates old user_subscriptions to new system")
    print("   3. Creates usage tracking and billing records")
    
    print("\n🔑 Step 3: Get JWT Token")
    print("   1. Go to Supabase Dashboard > Authentication > Users")
    print("   2. Find 'mohammed211920@gmail.com'")
    print("   3. Copy the JWT token")
    print("   4. Update TEST_JWT_TOKEN in this script")
    
    print("\n🚀 Step 4: Update FastAPI Application")
    print("   1. Update main.py to include new routers")
    print("   2. Import new models and services")
    print("   3. Start the server: python -m uvicorn app.main:app --reload")
    
    print("\n🧪 Step 5: Run This Test")
    print("   python test_new_subscription_system.py")
    
    print("\n📊 Expected Results:")
    print("   ✅ Health check: Should return healthy status")
    print("   ✅ Plans: Should show available subscription plans")
    print("   ✅ Subscription status: Should show current subscription details")
    print("   ✅ Feature usage: Should show usage limits and current usage")
    print("   ✅ Feature access: Should work based on subscription limits")
    print("   ✅ Usage tracking: Should increment and track feature usage")
    print("   ⚠️  Paid/Enterprise features: May fail based on current plan")

if __name__ == "__main__":
    print_setup_instructions()
    
    # Uncomment the line below to run the actual test
    # asyncio.run(test_new_subscription_system())
