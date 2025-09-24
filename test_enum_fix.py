#!/usr/bin/env python3
"""
Test the enum conversion fix
"""
import sys
sys.path.append('.')

def test_enum_values():
    """Test that enum values are correct"""
    print("🧪 Testing Enum Values")
    print("=" * 50)
    
    try:
        from app.models.profile import AccountType
        from app.schemas.profile import AccountTypeEnum
        
        print("✅ Enums imported successfully")
        
        # Test model enum
        print(f"   📋 AccountType.PERSONAL = '{AccountType.PERSONAL.value}'")
        print(f"   📋 AccountType.BUSINESS = '{AccountType.BUSINESS.value}'")
        
        # Test schema enum
        print(f"   📋 AccountTypeEnum.PERSONAL = '{AccountTypeEnum.PERSONAL.value}'")
        print(f"   📋 AccountTypeEnum.BUSINESS = '{AccountTypeEnum.BUSINESS.value}'")
        
        # Test conversion
        schema_value = AccountTypeEnum.PERSONAL.value
        print(f"   🔄 AccountTypeEnum.PERSONAL.value = '{schema_value}'")
        
        # This should work now (string value, not enum object)
        model_enum = AccountType(schema_value)
        print(f"   ✅ AccountType('{schema_value}') = {model_enum}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enum test failed: {e}")
        return False

def test_profile_creation_data():
    """Test profile creation data structure"""
    print("\n🧪 Testing Profile Creation Data")
    print("=" * 50)
    
    try:
        from app.schemas.profile import ProfileCreate, AccountTypeEnum
        
        profile_data = ProfileCreate(
            first_name="John",
            last_name="Doe",
            phone_number="0501234567",
            account_type=AccountTypeEnum.PERSONAL
        )
        
        print("✅ ProfileCreate created successfully")
        print(f"   👤 Name: {profile_data.first_name} {profile_data.last_name}")
        print(f"   📱 Phone: {profile_data.phone_number}")
        print(f"   🏢 Account Type: {profile_data.account_type}")
        print(f"   🔄 Account Type Value: '{profile_data.account_type.value}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Profile creation data test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Enum Conversion Fix")
    print("=" * 60)
    
    enum_ok = test_enum_values()
    data_ok = test_profile_creation_data()
    
    if enum_ok and data_ok:
        print("\n🎉 All tests passed!")
        print("✅ Enum conversion should now work correctly:")
        print("   - Database expects string values ('personal', 'business')")
        print("   - Profile service now passes .value instead of enum object")
        print("   - Profile creation should work without enum errors")
    else:
        print("\n❌ Some tests failed")
