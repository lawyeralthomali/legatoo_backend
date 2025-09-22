from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ProfileBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=1000)


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=1000)


class ProfileResponse(ProfileBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserAuth(BaseModel):
    """User authentication data from Supabase JWT"""
    id: UUID
    email: Optional[str] = None
    phone: Optional[str] = None
    aud: str = "authenticated"
    role: str = "authenticated"
    created_at: str
    updated_at: Optional[str] = None


class TokenData(BaseModel):
    """JWT token payload data"""
    sub: UUID  # User ID
    email: Optional[str] = None
    phone: Optional[str] = None
    aud: str = "authenticated"
    role: str = "authenticated"
    iat: int  # Issued at
    exp: int  # Expires at
    iss: str  # Issuer
    jti: Optional[str] = None  # JWT ID

