"""
User schemas for request/response models.

This module defines Pydantic schemas for user-related operations,
ensuring type safety and validation.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User's email address")
    is_active: bool = Field(True, description="Whether user is active")
    is_verified: bool = Field(False, description="Whether user is verified")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    is_verified: Optional[bool] = Field(None, description="Whether user is verified")


class UserResponse(UserBase):
    """Schema for user response data."""
    id: UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="User last update timestamp")
    
    class Config:
        from_attributes = True
