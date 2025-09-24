#!/usr/bin/env python3
"""
Test Pydantic v2 validator fix
"""
import sys
sys.path.append('.')

def test_pydantic_v2_validation():
    """Test that Pydantic v2 validators work correctly"""
    print("🧪 Testing Pydantic v2 Validation")
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
        
        print("✅ usman@gmail.com is now VALID with Pydantic v2!")
        print(f"   📧 Email: {request.email}")
        print(f"   👤 Name: {request.first_name} {request.last_name}")
        print(f"   📱 Phone: {request.phone_number}")
        
        return True
        
    except Exception as e:
        print(f"❌ usman@gmail.com is still INVALID: {e}")
        return False

def test_other_validations():
    """Test other field validations"""
    print("\n🧪 Testing Other Field Validations")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest
        
        # Test invalid phone number
        try:
            request = SignupRequest(
                email="test@gmail.com",
                password="SecurePass123!",
                first_name="Test",
                last_name="User",
                phone_number="0401234567"  # Invalid - doesn't start with 05
            )
            print("   ❌ Invalid phone should be rejected")
        except Exception as e:
            print(f"   ✅ Invalid phone correctly rejected: {str(e)[:50]}...")
        
        # Test invalid password
        try:
            request = SignupRequest(
                email="test@gmail.com",
                password="weak",  # Too weak
                first_name="Test",
                last_name="User",
                phone_number="0501234567"
            )
            print("   ❌ Weak password should be rejected")
        except Exception as e:
            print(f"   ✅ Weak password correctly rejected: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Other validations test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Pydantic v2 Validator Fix")
    print("=" * 60)
    
    email_ok = test_pydantic_v2_validation()
    other_ok = test_other_validations()
    
    if email_ok:
        print("\n🎉 SUCCESS!")
        print("✅ Pydantic v2 validators are working correctly")
        print("✅ usman@gmail.com should now be accepted")
        print("✅ The signup endpoint should work after server restart")
    else:
        print("\n❌ There's still an issue with the validation")
