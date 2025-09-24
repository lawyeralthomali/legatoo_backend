#!/usr/bin/env python3
"""
Simple email validation test
"""
import sys
sys.path.append('.')

def test_basic_email():
    """Test basic email validation"""
    print("🧪 Basic Email Test")
    print("=" * 30)
    
    try:
        from pydantic import BaseModel, EmailStr, ValidationError
        
        class SimpleEmailModel(BaseModel):
            email: EmailStr
        
        # Test usman@gmail.com
        try:
            model = SimpleEmailModel(email="usman@gmail.com")
            print("✅ usman@gmail.com is VALID")
            return True
        except ValidationError as e:
            print(f"❌ usman@gmail.com is INVALID: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_signup_request_directly():
    """Test SignupRequest directly"""
    print("\n🧪 SignupRequest Test")
    print("=" * 30)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest, ValidationError
        
        # Test with minimal valid data
        try:
            request = SignupRequest(
                email="usman@gmail.com",
                password="SecurePass123!",
                first_name="Usman",
                last_name="Test"
            )
            print("✅ SignupRequest with usman@gmail.com is VALID")
            return True
        except ValidationError as e:
            print(f"❌ SignupRequest with usman@gmail.com is INVALID: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Simple Email Validation Test")
    print("=" * 50)
    
    basic_ok = test_basic_email()
    signup_ok = test_signup_request_directly()
    
    if basic_ok and signup_ok:
        print("\n✅ usman@gmail.com should be valid")
    else:
        print("\n❌ There's an issue with usman@gmail.com")
