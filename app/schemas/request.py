"""
Request schemas for API endpoints.

This module defines all Pydantic request models used across the application,
ensuring consistent validation and type safety.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re
from ..models.profile import AccountType


class SignupRequest(BaseModel):
    """Request schema for user signup with comprehensive validation."""
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20, description="Must be Saudi (05xxxxxxxx)")
    account_type: Optional[AccountType] = Field(AccountType.PERSONAL, description="Account type")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format with detailed error messages"""
        if not v:
            raise ValueError("Email address is required")
        
        v = v.strip().lower()
        
        if not v:
            raise ValueError("Email address cannot be empty")
        
        if len(v) > 254:
            raise ValueError("Email address is too long (maximum 254 characters)")
        
        if '@' not in v:
            raise ValueError("Email address must contain '@' symbol")
        
        parts = v.split('@')
        if len(parts) != 2:
            raise ValueError("Email address must contain exactly one '@' symbol")
        
        local_part, domain_part = parts
        
        if not local_part:
            raise ValueError("Email address must have a local part before '@'")
        
        if len(local_part) > 64:
            raise ValueError("Local part of email is too long (maximum 64 characters)")
        
        if local_part.startswith('.') or local_part.endswith('.'):
            raise ValueError("Local part of email cannot start or end with a dot")
        
        if '..' in local_part:
            raise ValueError("Local part of email cannot contain consecutive dots")
        
        if not domain_part:
            raise ValueError("Email address must have a domain part after '@'")
        
        if len(domain_part) > 253:
            raise ValueError("Domain part of email is too long (maximum 253 characters)")
        
        if '.' not in domain_part:
            raise ValueError("Domain part must contain at least one dot")
        
        if domain_part.startswith('.') or domain_part.endswith('.'):
            raise ValueError("Domain part cannot start or end with a dot")
        
        if '..' in domain_part:
            raise ValueError("Domain part cannot contain consecutive dots")
        
        if not re.match(r'^[a-zA-Z0-9._+-]+$', local_part):
            raise ValueError("Local part contains invalid characters")
        
        if not re.match(r'^[a-zA-Z0-9.-]+$', domain_part):
            raise ValueError("Domain part contains invalid characters")
        
        tld = domain_part.split('.')[-1]
        if len(tld) < 2:
            raise ValueError("Domain must have a valid top-level domain")
        
        if not re.match(r'^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError("Email address format is invalid")
        
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure strong password policy"""
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate names format - supports English and Arabic characters"""
        if v:
            v = v.strip()
            # Allow English letters, Arabic characters (\u0600-\u06FF), spaces, hyphens, and apostrophes
            if not re.match(r"^[a-zA-Z\u0600-\u06FF\s\-']+$", v):
                raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")
            if len(v) < 1:
                raise ValueError("Name cannot be empty")
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate Saudi phone number format - must be exactly 10 digits starting with 05"""
        if v:
            digits = re.sub(r'\D', '', v)
            if len(digits) != 10:
                raise ValueError("Phone number must be exactly 10 digits")
            if not digits.startswith("05"):
                raise ValueError("Phone number must start with 05 (e.g., 0501234567)")
        return v


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation for login"""
        if not v or not v.strip():
            raise ValueError("Email address is required")
        return v.strip().lower()


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str = Field(..., description="Refresh token")


class ChangePasswordRequest(BaseModel):
    """Request schema for changing password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Ensure strong password policy for new password."""
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset."""
    email: str = Field(..., description="Email address for password reset")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation for password reset."""
        if not v or not v.strip():
            raise ValueError("Email address is required")
        return v.strip().lower()


class ConfirmPasswordResetRequest(BaseModel):
    """Request schema for confirming password reset."""
    reset_token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Ensure strong password policy for new password."""
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v


class ProfileUpdateRequest(BaseModel):
    """Request schema for profile updates."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=500)

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate names format - supports English and Arabic characters"""
        if v:
            v = v.strip()
            # Allow English letters, Arabic characters (\u0600-\u06FF), spaces, hyphens, and apostrophes
            if not re.match(r"^[a-zA-Z\u0600-\u06FF\s\-']+$", v):
                raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")
            if len(v) < 1:
                raise ValueError("Name cannot be empty")
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate Saudi phone number format - must be exactly 10 digits starting with 05"""
        if v:
            digits = re.sub(r'\D', '', v)
            if len(digits) != 10:
                raise ValueError("Phone number must be exactly 10 digits")
            if not digits.startswith("05"):
                raise ValueError("Phone number must start with 05 (e.g., 0501234567)")
        return v
