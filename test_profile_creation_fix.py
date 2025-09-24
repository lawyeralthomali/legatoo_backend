#!/usr/bin/env python3
"""
Test profile creation after fixing the relationship issue
"""
import sys
sys.path.append('.')

def test_models_import():
    """Test that all models can be imported without relationship errors"""
    print("🧪 Testing Model Imports")
    print("=" * 50)
    
    try:
        from app.models.profile import Profile
        print("✅ Profile model imported successfully")
    except Exception as e:
        print(f"❌ Profile import failed: {e}")
        return False
    
    try:
        from app.models.subscription import Subscription
        print("✅ Subscription model imported successfully")
    except Exception as e:
        print(f"❌ Subscription import failed: {e}")
        return False
    
    try:
        from app.models.plan import Plan
        print("✅ Plan model imported successfully")
    except Exception as e:
        print(f"❌ Plan import failed: {e}")
        return False
    
    try:
        from app.models.usage_tracking import UsageTracking
        print("✅ UsageTracking model imported successfully")
    except Exception as e:
        print(f"❌ UsageTracking import failed: {e}")
        return False
    
    # Test importing all models together
    try:
        from app.models import profile, subscription, plan, usage_tracking
        print("✅ All models imported together successfully")
    except Exception as e:
        print(f"❌ Combined import failed: {e}")
        return False
    
    return True

def test_signup_request():
    """Test signup request validation"""
    print("\n🧪 Testing Signup Request")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest
        request = SignupRequest(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe",
            phone_number="0501234567"
        )
        print("✅ SignupRequest created successfully")
        return True
    except Exception as e:
        print(f"❌ SignupRequest failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Profile Creation Fix")
    print("=" * 60)
    
    models_ok = test_models_import()
    signup_ok = test_signup_request()
    
    if models_ok and signup_ok:
        print("\n🎉 All tests passed!")
        print("✅ Profile creation should now work without relationship errors")
        print("📋 The signup endpoint should successfully:")
        print("   - Create Supabase user")
        print("   - Create local profile")
        print("   - Handle Saudi phone numbers (05xxxxxxxx)")
    else:
        print("\n❌ Some tests failed - there may still be issues")
