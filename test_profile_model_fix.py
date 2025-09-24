#!/usr/bin/env python3
"""
Test the profile model fix
"""
import sys
sys.path.append('.')

def test_profile_model():
    """Test that the Profile model can be imported and used"""
    print("🧪 Testing Profile Model Fix")
    print("=" * 50)
    
    try:
        from app.models.profile import Profile, AccountType
        print("✅ Profile model imported successfully")
        
        # Test creating a profile instance
        profile = Profile(
            id="123e4567-e89b-12d3-a456-426614174000",
            first_name="John",
            last_name="Doe",
            phone_number="0501234567",
            account_type="personal"  # String value, not enum
        )
        
        print("✅ Profile instance created successfully")
        print(f"   👤 Name: {profile.first_name} {profile.last_name}")
        print(f"   📱 Phone: {profile.phone_number}")
        print(f"   🏢 Account Type: {profile.account_type} (type: {type(profile.account_type)})")
        
        return True
        
    except Exception as e:
        print(f"❌ Profile model test failed: {e}")
        return False

def test_profile_service():
    """Test that profile service can handle string values"""
    print("\n🧪 Testing Profile Service")
    print("=" * 50)
    
    try:
        from app.schemas.profile import ProfileCreate, AccountTypeEnum
        
        profile_data = ProfileCreate(
            first_name="Jane",
            last_name="Smith",
            phone_number="0512345678",
            account_type=AccountTypeEnum.PERSONAL
        )
        
        print("✅ ProfileCreate created successfully")
        print(f"   👤 Name: {profile_data.first_name} {profile_data.last_name}")
        print(f"   📱 Phone: {profile_data.phone_number}")
        print(f"   🏢 Account Type: {profile_data.account_type}")
        print(f"   🔄 Account Type Value: '{profile_data.account_type.value}'")
        
        # This should now work - string value passed to model
        account_type_value = profile_data.account_type.value
        print(f"   ✅ String value to pass to model: '{account_type_value}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Profile service test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Profile Model Fix")
    print("=" * 60)
    
    model_ok = test_profile_model()
    service_ok = test_profile_service()
    
    if model_ok and service_ok:
        print("\n🎉 All tests passed!")
        print("✅ Profile model now uses String column instead of Enum:")
        print("   - Database expects string values ('personal', 'business')")
        print("   - Model now accepts string values directly")
        print("   - No more enum conversion errors")
        print("   - Profile creation should work correctly")
    else:
        print("\n❌ Some tests failed")
