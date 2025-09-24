"""
Tests for signup validation
"""
import pytest
from pydantic import ValidationError
from app.routes.supabase_auth_router import SignupRequest


def test_valid_signup_request():
    """Test valid signup request"""
    valid_data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890"
    }
    
    request = SignupRequest(**valid_data)
    assert request.email == "test@example.com"
    assert request.password == "SecurePass123!"
    assert request.first_name == "John"
    assert request.last_name == "Doe"
    assert request.phone_number == "+1234567890"


def test_minimal_valid_signup_request():
    """Test minimal valid signup request"""
    valid_data = {
        "email": "user@example.com",
        "password": "MyP@ssw0rd",
        "first_name": "User"
    }
    
    request = SignupRequest(**valid_data)
    assert request.email == "user@example.com"
    assert request.password == "MyP@ssw0rd"
    assert request.first_name == "User"
    assert request.last_name is None
    assert request.phone_number is None


def test_password_validation():
    """Test password validation rules"""
    # Valid passwords
    valid_passwords = [
        "SecurePass123!",
        "MyP@ssw0rd",
        "StrongP@ss1",
        "ComplexP@ssw0rd!"
    ]
    
    for password in valid_passwords:
        request = SignupRequest(
            email="test@example.com",
            password=password,
            first_name="Test"
        )
        assert request.password == password
    
    # Invalid passwords
    invalid_passwords = [
        "weak",  # Too short
        "password",  # No uppercase, digit, or special char
        "PASSWORD123",  # No lowercase or special char
        "password123",  # No uppercase or special char
        "Password"  # No digit or special char
    ]
    
    for password in invalid_passwords:
        with pytest.raises(ValidationError):
            SignupRequest(
                email="test@example.com",
                password=password,
                first_name="Test"
            )


def test_email_validation():
    """Test email validation"""
    # Valid emails
    valid_emails = [
        "test@example.com",
        "user@company.org",
        "test+tag@gmail.com"
    ]
    
    for email in valid_emails:
        request = SignupRequest(
            email=email,
            password="SecurePass123!",
            first_name="Test"
        )
        assert request.email == email
    
    # Invalid emails (disposable)
    disposable_emails = [
        "user@tempmail.org",
        "user@10minutemail.com",
        "user@guerrillamail.com"
    ]
    
    for email in disposable_emails:
        with pytest.raises(ValidationError):
            SignupRequest(
                email=email,
                password="SecurePass123!",
                first_name="Test"
            )


def test_name_validation():
    """Test first name and last name validation"""
    # Valid names
    valid_names = [
        "John",
        "Mary-Jane",
        "O'Connor",
        "Jean Paul",
        "García-López"
    ]
    
    for name in valid_names:
        request = SignupRequest(
            email="test@example.com",
            password="SecurePass123!",
            first_name=name
        )
        assert request.first_name == name
    
    # Invalid names
    invalid_names = [
        "John123",  # Contains numbers
        "John@Doe",  # Contains special chars
        "John--Doe",  # Consecutive hyphens
        "John  Doe",  # Consecutive spaces
        "",  # Empty
        "   "  # Only whitespace
    ]
    
    for name in invalid_names:
        with pytest.raises(ValidationError):
            SignupRequest(
                email="test@example.com",
                password="SecurePass123!",
                first_name=name
            )


def test_phone_number_validation():
    """Test Saudi phone number validation"""
    # Valid Saudi phone numbers
    valid_phones = [
        "0501234567",
        "0512345678",
        "0523456789",
        "0534567890",
        "0545678901",
        "0556789012",
        "0567890123",
        "0578901234",
        "0589012345",
        "0590123456"
    ]
    
    for phone in valid_phones:
        request = SignupRequest(
            email="test@example.com",
            password="SecurePass123!",
            first_name="Test",
            phone_number=phone
        )
        assert request.phone_number == phone
    
    # Invalid phone numbers
    invalid_phones = [
        "123456789",  # Too short (9 digits)
        "12345678901",  # Too long (11 digits)
        "0401234567",  # Doesn't start with 05
        "0601234567",  # Doesn't start with 05
        "abc123def",  # Contains letters
        "0123456789",  # Starts with 01 instead of 05
        "050123456",  # Too short (9 digits)
        "05012345678"  # Too long (11 digits)
    ]
    
    for phone in invalid_phones:
        with pytest.raises(ValidationError):
            SignupRequest(
                email="test@example.com",
                password="SecurePass123!",
                first_name="Test",
                phone_number=phone
            )


def test_optional_fields():
    """Test that optional fields work correctly"""
    # All fields provided
    request = SignupRequest(
        email="test@example.com",
        password="SecurePass123!",
        first_name="John",
        last_name="Doe",
        phone_number="+1234567890"
    )
    assert request.first_name == "John"
    assert request.last_name == "Doe"
    assert request.phone_number == "+1234567890"
    
    # Only required fields
    request = SignupRequest(
        email="test@example.com",
        password="SecurePass123!"
    )
    assert request.first_name is None
    assert request.last_name is None
    assert request.phone_number is None


def test_whitespace_trimming():
    """Test that names are trimmed of whitespace"""
    request = SignupRequest(
        email="test@example.com",
        password="SecurePass123!",
        first_name="  John  ",
        last_name="  Doe  "
    )
    assert request.first_name == "John"
    assert request.last_name == "Doe"
