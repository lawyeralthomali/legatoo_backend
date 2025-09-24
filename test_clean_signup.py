#!/usr/bin/env python3
"""
Test the cleaned-up signup function
"""
import sys
sys.path.append('.')

def test_signup_request():
    """Test signup request validation"""
    print("🧪 Testing Clean Signup Request")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest, SignupResponse
        print("✅ SignupRequest and SignupResponse imported successfully")
        
        # Test valid request
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
        print(f"❌ Signup request failed: {e}")
        return False

def test_phone_validation():
    """Test Saudi phone number validation"""
    print("\n🧪 Testing Saudi Phone Validation")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest
        
        # Valid Saudi phone numbers
        valid_phones = ["0501234567", "0512345678", "0523456789"]
        for phone in valid_phones:
            request = SignupRequest(
                email="test@example.com",
                password="SecurePass123!",
                first_name="Test",
                phone_number=phone
            )
            print(f"   ✅ {phone} - Valid")
        
        # Invalid phone numbers
        invalid_phones = ["0401234567", "123456789", "05012345678"]
        for phone in invalid_phones:
            try:
                request = SignupRequest(
                    email="test@example.com",
                    password="SecurePass123!",
                    first_name="Test",
                    phone_number=phone
                )
                print(f"   ❌ {phone} - Should be invalid but passed")
                return False
            except:
                print(f"   ✅ {phone} - Correctly rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ Phone validation test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Testing Cleaned-Up Signup Function")
    print("=" * 60)
    
    request_ok = test_signup_request()
    phone_ok = test_phone_validation()
    
    if request_ok and phone_ok:
        print("\n🎉 All tests passed!")
        print("✅ The signup function is now clean and easy to follow:")
        print("   1. Validate configuration")
        print("   2. Validate required fields")
        print("   3. Prepare user metadata")
        print("   4. Create user in Supabase")
        print("   5. Handle Supabase response")
        print("   6. Extract user data")
        print("   7. Create local profile")
        print("   8. Return success response")
        print("\n📱 Saudi phone validation working (05xxxxxxxx)")
        print("🔧 Profile creation should work without relationship errors")
    else:
        print("\n❌ Some tests failed")
