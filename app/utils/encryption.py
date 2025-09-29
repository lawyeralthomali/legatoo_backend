"""
Encryption utilities for sensitive data.

This module provides functions for encrypting and decrypting
sensitive information like Enjaz credentials.
"""

from cryptography.fernet import Fernet
from typing import Optional
import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv("supabase.env")

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Generate a new key if none exists (for development)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"⚠️  WARNING: No ENCRYPTION_KEY found. Generated new key: {ENCRYPTION_KEY}")
    print("Please add this key to your supabase.env file for production use.")
else:
    # Convert string key to bytes if it's a string
    if isinstance(ENCRYPTION_KEY, str):
        ENCRYPTION_KEY = ENCRYPTION_KEY.encode()

# Create Fernet cipher suite
cipher_suite = Fernet(ENCRYPTION_KEY)


def encrypt_data(data: str) -> str:
    """
    Encrypt a string using Fernet symmetric encryption.
    
    Args:
        data: The string to encrypt
        
    Returns:
        str: Base64 encoded encrypted data
        
    Raises:
        ValueError: If data is empty or None
    """
    if not data:
        raise ValueError("Data cannot be empty or None")
    
    # Convert string to bytes and encrypt
    encrypted_bytes = cipher_suite.encrypt(data.encode('utf-8'))
    
    # Encode as base64 string for database storage
    return base64.b64encode(encrypted_bytes).decode('utf-8')


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt a string that was encrypted with encrypt_data.
    
    Args:
        encrypted_data: Base64 encoded encrypted data
        
    Returns:
        str: Decrypted original string
        
    Raises:
        ValueError: If encrypted_data is empty, None, or invalid
    """
    if not encrypted_data:
        raise ValueError("Encrypted data cannot be empty or None")
    
    try:
        # Decode base64 and decrypt
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        decrypted_bytes = cipher_suite.decrypt(encrypted_bytes)
        
        # Convert back to string
        return decrypted_bytes.decode('utf-8')
        
    except Exception as e:
        raise ValueError(f"Failed to decrypt data: {str(e)}")


def generate_encryption_key() -> str:
    """
    Generate a new encryption key for use in environment variables.
    
    Returns:
        str: A new Fernet encryption key
    """
    return Fernet.generate_key().decode()
