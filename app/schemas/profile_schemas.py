"""
Profile schemas for API requests and responses.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..models.profile import AccountType


class ProfileBase(BaseModel):
    """Base profile schema."""
    first_name: str
    last_name: str
    phone_number: Optional[str] = None


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""
    email: EmailStr
    account_type: Optional[AccountType] = AccountType.PERSONAL


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
    
    class Config:
        from_attributes = True


# Additional schemas that were in the old profile.py
class TokenData(BaseModel):
    """Schema for JWT token data."""
    user_id: str
    email: str
    aud: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    sub: Optional[str] = None


class UserAuth(BaseModel):
    """Schema for authenticated user data."""
    user_id: str
    email: str
    aud: Optional[str] = None
    role: Optional[str] = None
    profile: Optional[dict] = None
