#!/usr/bin/env python3
"""
Test without email validation to isolate the issue
"""
import sys
sys.path.append('.')

def test_no_email_validation():
    """Test that usman@gmail.com works without email validation"""
    print("🧪 Testing Without Email Validation")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest
        
        # Test usman@gmail.com
        request = SignupRequest(
            email="usman@gmail.com",
            password="SecurePass123!",
            first_name="Usman",
            last_name="Test",
            phone_number="0501234567"
        )
        
        print("✅ usman@gmail.com is VALID without email validation!")
        print(f"   📧 Email: {request.email}")
        print(f"   👤 Name: {request.first_name} {request.last_name}")
        print(f"   📱 Phone: {request.phone_number}")
        
        return True
        
    except Exception as e:
        print(f"❌ usman@gmail.com is still INVALID: {e}")
        print(f"   Error type: {type(e)}")
        print(f"   Error details: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Without Email Validation")
    print("=" * 60)
    
    success = test_no_email_validation()
    
    if success:
        print("\n🎉 SUCCESS!")
        print("✅ Email validation was the issue")
        print("✅ usman@gmail.com works without custom validation")
        print("✅ The signup endpoint should work now")
    else:
        print("\n❌ The issue is NOT with email validation")
        print("🔍 There's another validation layer causing the problem")
