#!/usr/bin/env python3
"""
Test Saudi phone number validation
"""
import sys
sys.path.append('.')

def test_saudi_phone_validation():
    """Test the new Saudi phone number validation"""
    print("🧪 Testing Saudi Phone Number Validation")
    print("=" * 50)
    
    try:
        from app.routes.supabase_auth_router import SignupRequest
        print("✅ SignupRequest imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test valid Saudi phone numbers
    print("\n📱 Testing Valid Saudi Phone Numbers:")
    valid_phones = [
        "0501234567",
        "0512345678", 
        "0523456789",
        "0534567890",
        "0545678901"
    ]
    
    for phone in valid_phones:
        try:
            request = SignupRequest(
                email="test@example.com",
                password="SecurePass123!",
                first_name="Test",
                phone_number=phone
            )
            print(f"   ✅ {phone} - Valid")
        except Exception as e:
            print(f"   ❌ {phone} - Invalid: {e}")
            return False
    
    # Test invalid phone numbers
    print("\n❌ Testing Invalid Phone Numbers:")
    invalid_phones = [
        ("123456789", "Too short (9 digits)"),
        ("12345678901", "Too long (11 digits)"),
        ("0401234567", "Doesn't start with 05"),
        ("0601234567", "Doesn't start with 05"),
        ("050123456", "Too short (9 digits)"),
        ("05012345678", "Too long (11 digits)")
    ]
    
    for phone, reason in invalid_phones:
        try:
            request = SignupRequest(
                email="test@example.com",
                password="SecurePass123!",
                first_name="Test",
                phone_number=phone
            )
            print(f"   ❌ {phone} - Should be invalid but passed: {reason}")
            return False
        except Exception as e:
            print(f"   ✅ {phone} - Correctly rejected: {reason}")
    
    print("\n🎉 All Saudi phone number validation tests passed!")
    return True

if __name__ == "__main__":
    success = test_saudi_phone_validation()
    if success:
        print("\n🚀 Saudi phone number validation is working correctly!")
    else:
        print("\n❌ There are issues with the phone number validation")
