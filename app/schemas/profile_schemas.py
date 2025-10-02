"""
Profile schemas for API requests and responses.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, Union
from datetime import datetime
from uuid import UUID
from ..models.profile import AccountType
from ..models.role import UserRole


class ProfileBase(BaseModel):
    """Base profile schema."""
    first_name: str
    last_name: str
    phone_number: Optional[str] = None


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""
    email: EmailStr
    account_type: Optional[AccountType] = AccountType.PERSONAL
    
    def model_dump(self, **kwargs):
        """Override model_dump to serialize AccountType enum to string."""
        data = super().model_dump(**kwargs)
        if 'account_type' in data and isinstance(data['account_type'], AccountType):
            data['account_type'] = data['account_type'].value
        return data


class ProfileUpdate(ProfileBase):
    """Schema for updating profile information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    account_type: Optional[AccountType] = None
    
    def model_dump(self, **kwargs):
        """Override model_dump to serialize AccountType enum to string."""
        data = super().model_dump(**kwargs)
        if 'account_type' in data and isinstance(data['account_type'], AccountType):
            data['account_type'] = data['account_type'].value
        return data


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
    sub: Union[UUID, int]  # User ID (supports both UUID and Integer)
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
