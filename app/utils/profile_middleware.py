"""
Middleware and utilities for automatic profile management
"""
from fastapi import Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from uuid import UUID

from ..utils.auth import get_current_user_id
from ..utils.profile_creation import ensure_user_profile
from ..models.profile import AccountType


async def ensure_profile_middleware(request: Request, call_next):
    """
    Middleware to ensure authenticated users have profiles
    
    This middleware can be added to FastAPI app to automatically
    create profiles for authenticated users who don't have one.
    """
    # Only process authenticated requests
    if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/auth/"):
        try:
            # Get current user ID from token
            user_id = await get_current_user_id(request)
            if user_id:
                # Get database session
                db: AsyncSession = request.state.db
                
                # Ensure profile exists
                profile_result = await ensure_user_profile(
                    db=db,
                    user_id=user_id,
                    account_type=AccountType.PERSONAL
                )
                
                # Add profile info to request state
                request.state.profile = profile_result["profile"]
                request.state.profile_created = profile_result["created"]
                
        except Exception as e:
            # If profile creation fails, log but don't block the request
            print(f"Profile middleware warning: {str(e)}")
    
    response = await call_next(request)
    return response


async def get_user_profile_or_create(
    db: AsyncSession,
    user_id: UUID,
    **profile_data
) -> Dict[str, Any]:
    """
    Get user profile or create one if it doesn't exist
    
    This is a convenience function that can be used in any endpoint
    to ensure a user has a profile.
    
    Args:
        db: Database session
        user_id: User's UUID
        **profile_data: Optional profile data
        
    Returns:
        Dict containing profile information
    """
    return await ensure_user_profile(
        db=db,
        user_id=user_id,
        **profile_data
    )


async def require_profile(
    db: AsyncSession,
    user_id: UUID,
    **profile_data
) -> Dict[str, Any]:
    """
    Require a profile to exist for the user, create one if needed
    
    This function will always return a profile, creating one if necessary.
    
    Args:
        db: Database session
        user_id: User's UUID
        **profile_data: Optional profile data
        
    Returns:
        Dict containing profile information
        
    Raises:
        HTTPException: If profile creation fails
    """
    result = await ensure_user_profile(
        db=db,
        user_id=user_id,
        **profile_data
    )
    
    if not result["profile"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create or retrieve user profile"
        )
    
    return result
