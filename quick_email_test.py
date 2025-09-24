#!/usr/bin/env python3
"""
Quick test to verify email validation
"""
import sys
sys.path.append('.')

def test_current_validation():
    """Test current email validation"""
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
        
        print("✅ usman@gmail.com is VALID with current code")
        print(f"Email field type: {type(request.email)}")
        print(f"Email value: {request.email}")
        return True
        
    except Exception as e:
        print(f"❌ usman@gmail.com is INVALID: {e}")
        return False

if __name__ == "__main__":
    test_current_validation()
