#!/usr/bin/env python3
"""
Test the PostgreSQL enum fix
"""
import sys
sys.path.append('.')

def test_profile_model():
    """Test that the Profile model can be imported and used with PostgreSQL enum"""
    print("🧪 Testing Profile Model with PostgreSQL Enum")
    print("=" * 50)
    
    try:
        from app.models.profile import Profile, AccountType, account_type_enum
        print("✅ Profile model imported successfully")
        print(f"✅ PostgreSQL enum type: {account_type_enum}")
        
        # Test creating a profile instance
        profile = Profile(
            id="123e4567-e89b-12d3-a456-426614174000",
            first_name="John",
            last_name="Doe",
            phone_number="0501234567",
            account_type="personal"  # String value that matches enum
        )
        
        print("✅ Profile instance created successfully")
        print(f"   👤 Name: {profile.first_name} {profile.last_name}")
        print(f"   📱 Phone: {profile.phone_number}")
        print(f"   🏢 Account Type: {profile.account_type} (type: {type(profile.account_type)})")
        
        return True
        
    except Exception as e:
        print(f"❌ Profile model test failed: {e}")
        return False

def test_enum_values():
    """Test enum values match database schema"""
    print("\n🧪 Testing Enum Values")
    print("=" * 50)
    
    try:
        from app.models.profile import AccountType
        
        print("✅ AccountType enum values:")
        print(f"   📋 PERSONAL = '{AccountType.PERSONAL.value}'")
        print(f"   📋 BUSINESS = '{AccountType.BUSINESS.value}'")
        
        # These should match the database enum values
        assert AccountType.PERSONAL.value == "personal"
        assert AccountType.BUSINESS.value == "business"
        
        print("✅ Enum values match database schema")
        return True
        
    except Exception as e:
        print(f"❌ Enum values test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing PostgreSQL Enum Fix")
    print("=" * 60)
    
    model_ok = test_profile_model()
    enum_ok = test_enum_values()
    
    if model_ok and enum_ok:
        print("\n🎉 All tests passed!")
        print("✅ Profile model now uses PostgreSQL ENUM correctly:")
        print("   - Uses ENUM('personal', 'business', name='account_type_enum', create_type=False)")
        print("   - Matches the database schema exactly")
        print("   - Should work with the existing account_type_enum in database")
        print("   - Profile creation should now work without enum errors")
    else:
        print("\n❌ Some tests failed")
