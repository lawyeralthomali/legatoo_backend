"""
Profile schemas for API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re
from ..models.profile import AccountType
from ..models.role import UserRole


class ProfileBase(BaseModel):
    """Base profile schema."""
    first_name: str
    last_name: str
    phone_number: Optional[str] = None


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""
    email: str = Field(..., description="Valid email address")
    account_type: Optional[AccountType] = AccountType.PERSONAL

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        if not v or not v.strip():
            raise ValueError("Email address is required")
        
        v = v.strip().lower()
        
        # Basic email validation
        if not re.match(r'^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError("Invalid email format")
        
        return v


class ProfileUpdate(ProfileBase):
    """Schema for updating profile information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    account_type: Optional[AccountType] = None


class ProfileResponse(ProfileBase):
    """Schema for profile response."""
    id: int
    email: str
    avatar_url: Optional[str] = None
    account_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Additional schemas that were in the old profile.py
class TokenData(BaseModel):
    """Schema for JWT token data."""
    sub: UUID  # User ID
    email: Optional[str] = None
    phone: Optional[str] = None
    aud: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    iss: Optional[str] = None
    jti: Optional[str] = None


class UserAuth(BaseModel):
    """Schema for authenticated user data."""
    user_id: str
    email: str
    aud: Optional[str] = None
    role: Optional[str] = None
    profile: Optional[dict] = None
