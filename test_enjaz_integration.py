"""
Test script for Enjaz integration functionality.

This script demonstrates how to use the Enjaz integration features.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.encryption import encrypt_data, decrypt_data, generate_encryption_key
from app.schemas.enjaz_schemas import EnjazCredentialsRequest, CaseData


async def test_encryption():
    """Test encryption and decryption functionality."""
    print("🔐 Testing Encryption/Decryption...")
    
    # Test data
    original_username = "test_user@enjaz.gov.sa"
    original_password = "test_password_123"
    
    try:
        # Encrypt
        encrypted_username = encrypt_data(original_username)
        encrypted_password = encrypt_data(original_password)
        
        print(f"✅ Original username: {original_username}")
        print(f"✅ Encrypted username: {encrypted_username[:50]}...")
        print(f"✅ Original password: {original_password}")
        print(f"✅ Encrypted password: {encrypted_password[:50]}...")
        
        # Decrypt
        decrypted_username = decrypt_data(encrypted_username)
        decrypted_password = decrypt_data(encrypted_password)
        
        print(f"✅ Decrypted username: {decrypted_username}")
        print(f"✅ Decrypted password: {decrypted_password}")
        
        # Verify
        assert original_username == decrypted_username
        assert original_password == decrypted_password
        
        print("✅ Encryption/Decryption test passed!\n")
        
    except Exception as e:
        print(f"❌ Encryption test failed: {str(e)}\n")


def test_schemas():
    """Test Pydantic schemas."""
    print("📋 Testing Pydantic Schemas...")
    
    try:
        # Test EnjazCredentialsRequest
        credentials = EnjazCredentialsRequest(
            username="test_user@enjaz.gov.sa",
            password="test_password_123"
        )
        
        print(f"✅ Credentials schema: {credentials.username}")
        
        # Test CaseData
        case_data = CaseData(
            case_number="CASE-2024-001",
            case_type="Civil",
            status="Active",
            additional_data={"priority": "High", "assigned_to": "Lawyer Smith"}
        )
        
        print(f"✅ Case data schema: {case_data.case_number}")
        print("✅ Schema validation test passed!\n")
        
    except Exception as e:
        print(f"❌ Schema test failed: {str(e)}\n")


async def test_enjaz_bot():
    """Test Enjaz bot functionality (mock test)."""
    print("🤖 Testing Enjaz Bot (Mock)...")
    
    try:
        from app.utils.enjaz_bot import EnjazBot
        
        # Test bot initialization
        bot = EnjazBot(headless=True)
        print("✅ EnjazBot initialized successfully")
        
        # Test context manager
        async with EnjazBot(headless=True) as bot:
            print("✅ EnjazBot context manager working")
            
        print("✅ Enjaz Bot test passed!\n")
        
    except Exception as e:
        print(f"❌ Enjaz Bot test failed: {str(e)}\n")


def test_generate_encryption_key():
    """Test encryption key generation."""
    print("🔑 Testing Encryption Key Generation...")
    
    try:
        key = generate_encryption_key()
        print(f"✅ Generated encryption key: {key[:20]}...")
        print(f"✅ Key length: {len(key)} characters")
        print("✅ Encryption key generation test passed!\n")
        
    except Exception as e:
        print(f"❌ Encryption key generation test failed: {str(e)}\n")


async def main():
    """Run all tests."""
    print("🚀 Starting Enjaz Integration Tests\n")
    
    # Test encryption
    await test_encryption()
    
    # Test schemas
    test_schemas()
    
    # Test bot
    await test_enjaz_bot()
    
    # Test key generation
    test_generate_encryption_key()
    
    print("🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
