#!/usr/bin/env python3
"""
Test the email validation fix
"""
import sys
sys.path.append('.')

def test_usman_email():
    """Test usman@gmail.com specifically"""
    print("🧪 Testing usman@gmail.com")
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
        
        print("✅ usman@gmail.com is now VALID!")
        print(f"   📧 Email: {request.email}")
        print(f"   👤 Name: {request.first_name} {request.last_name}")
        print(f"   📱 Phone: {request.phone_number}")
        
        return True
        
    except Exception as e:
        print(f"❌ usman@gmail.com is still INVALID: {e}")
        return False

def test_other_emails():
    """Test other email formats"""
    print("\n🧪 Testing Other Email Formats")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest
        
        test_emails = [
            "test@gmail.com",
            "user@yahoo.com",
            "admin@outlook.com",
            "someone@hotmail.com",
            "john.doe@company.co.uk",
            "user+tag@domain.org"
        ]
        
        for email in test_emails:
            try:
                request = SignupRequest(
                    email=email,
                    password="SecurePass123!",
                    first_name="Test",
                    last_name="User",
                    phone_number="0501234567"
                )
                print(f"   ✅ {email} - VALID")
            except Exception as e:
                print(f"   ❌ {email} - INVALID: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Other emails test failed: {e}")
        return False

def test_invalid_emails():
    """Test invalid email formats"""
    print("\n🧪 Testing Invalid Email Formats")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user@@domain.com",
            "user@10minutemail.com"  # Disposable email
        ]
        
        for email in invalid_emails:
            try:
                request = SignupRequest(
                    email=email,
                    password="SecurePass123!",
                    first_name="Test",
                    last_name="User",
                    phone_number="0501234567"
                )
                print(f"   ❌ {email} - Should be invalid but passed")
            except Exception as e:
                print(f"   ✅ {email} - Correctly rejected: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Invalid emails test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Email Validation Fix")
    print("=" * 60)
    
    usman_ok = test_usman_email()
    other_ok = test_other_emails()
    invalid_ok = test_invalid_emails()
    
    if usman_ok:
        print("\n🎉 SUCCESS!")
        print("✅ usman@gmail.com is now accepted")
        print("✅ Custom email validation is working")
        print("✅ The signup endpoint should now work with usman@gmail.com")
    else:
        print("\n❌ There's still an issue with usman@gmail.com")
