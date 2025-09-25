"""
Profile schemas for request/response models.

This module defines Pydantic schemas for profile-related operations,
ensuring type safety and validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum
import re


class AccountTypeEnum(str, Enum):
    """Account type enumeration for Pydantic"""
    PERSONAL = "personal"
    BUSINESS = "business"


class ProfileBase(BaseModel):
    """Base profile schema with common fields."""
    email: str = Field(..., description="User's email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    avatar_url: Optional[str] = Field(None, max_length=500, description="User's avatar URL")
    phone_number: Optional[str] = Field(None, max_length=20, description="User's phone number")
    account_type: AccountTypeEnum = Field(default=AccountTypeEnum.PERSONAL, description="Account type")


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""
    pass


class ProfileUpdate(BaseModel):
    """Schema for updating profile information."""
    email: Optional[str] = Field(None, description="User's email address")
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User's last name")
    avatar_url: Optional[str] = Field(None, max_length=500, description="User's avatar URL")
    phone_number: Optional[str] = Field(None, max_length=20, description="User's phone number")
    account_type: Optional[AccountTypeEnum] = Field(None, description="Account type")

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate names format"""
        if v:
            v = v.strip()
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")
            if len(v) < 1:
                raise ValueError("Name cannot be empty")
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate Saudi phone number format"""
        if v:
            digits = re.sub(r'\D', '', v)
            if len(digits) != 10 or not digits.startswith("05"):
                raise ValueError("Phone number must be Saudi format: 05xxxxxxxx")
        return v


class ProfileResponse(ProfileBase):
    """Schema for profile response data."""
    id: UUID = Field(..., description="Profile ID (same as Supabase user_id)")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Profile last update timestamp")
    
    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Schema for JWT token data."""
    user_id: str = Field(..., description="User ID from token")
    email: str = Field(..., description="User email from token")
    aud: Optional[str] = Field(None, description="Token audience")
    role: Optional[str] = Field(None, description="User role")
    exp: Optional[int] = Field(None, description="Token expiration timestamp")
    iat: Optional[int] = Field(None, description="Token issued at timestamp")
    sub: Optional[str] = Field(None, description="Token subject")


class UserAuth(BaseModel):
    """Schema for authenticated user data."""
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    aud: Optional[str] = Field(None, description="Token audience")
    role: Optional[str] = Field(None, description="User role")
    profile: Optional[dict] = Field(None, description="User profile data")