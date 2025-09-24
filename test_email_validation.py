#!/usr/bin/env python3
"""
Test email validation to see why usman@gmail.com is invalid
"""
import sys
sys.path.append('.')

def test_email_validation():
    """Test email validation with usman@gmail.com"""
    print("🧪 Testing Email Validation")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest
        print("✅ SignupRequest imported successfully")
        
        # Test with usman@gmail.com
        test_email = "usman@gmail.com"
        print(f"📧 Testing email: {test_email}")
        
        try:
            request = SignupRequest(
                email=test_email,
                password="SecurePass123!",
                first_name="Usman",
                last_name="Test",
                phone_number="0501234567"
            )
            print(f"✅ Email '{test_email}' is VALID")
            return True
            
        except Exception as e:
            print(f"❌ Email '{test_email}' is INVALID: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
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
            "someone@hotmail.com"
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

def test_pydantic_email():
    """Test Pydantic EmailStr directly"""
    print("\n🧪 Testing Pydantic EmailStr")
    print("=" * 50)
    
    try:
        from pydantic import EmailStr, ValidationError
        
        test_email = "usman@gmail.com"
        print(f"📧 Testing Pydantic EmailStr with: {test_email}")
        
        try:
            email_obj = EmailStr(test_email)
            print(f"✅ Pydantic EmailStr accepts: {email_obj}")
            return True
        except ValidationError as e:
            print(f"❌ Pydantic EmailStr rejects: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Pydantic EmailStr test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging Email Validation Issue")
    print("=" * 60)
    
    email_ok = test_email_validation()
    other_ok = test_other_emails()
    pydantic_ok = test_pydantic_email()
    
    if not email_ok:
        print("\n❌ usman@gmail.com is being rejected")
        print("🔍 Check the specific error message above")
    else:
        print("\n✅ usman@gmail.com should be valid")
        print("🔍 The issue might be elsewhere")
