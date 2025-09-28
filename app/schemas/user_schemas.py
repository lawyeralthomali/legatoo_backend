"""
User schemas for API requests and responses.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from ..models.role import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_verified: bool
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin only)."""
    role: UserRole
