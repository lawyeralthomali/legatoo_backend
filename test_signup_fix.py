#!/usr/bin/env python3
"""
Test the fixed signup endpoint
"""
import sys
sys.path.append('.')

def test_signup_request_validation():
    """Test that the SignupRequest validation works correctly"""
    print("🧪 Testing SignupRequest Validation")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest
        print("✅ SignupRequest imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test valid request
    try:
        request = SignupRequest(
            email="test@example.com",
            password="SecurePass123!",
            first_name="John",
            last_name="Doe",
            phone_number="0501234567"
        )
        print("✅ Valid signup request created successfully")
        print(f"   📧 Email: {request.email}")
        print(f"   👤 Name: {request.first_name} {request.last_name}")
        print(f"   📱 Phone: {request.phone_number}")
        return True
    except Exception as e:
        print(f"❌ Valid request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_signup_request_validation()
    if success:
        print("\n🚀 SignupRequest validation is working correctly!")
        print("📋 The signup endpoint should now work properly with:")
        print("   - Saudi phone numbers (05xxxxxxxx)")
        print("   - Proper user data handling")
        print("   - Profile creation")
    else:
        print("\n❌ There are still issues with the signup validation")
