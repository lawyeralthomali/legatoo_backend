"""
Utility functions for profile creation and management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from uuid import UUID

from ..services.profile_service import ProfileService
from ..models.profile import AccountType


async def ensure_user_profile(
    db: AsyncSession,
    user_id: UUID,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    avatar_url: Optional[str] = None,
    account_type: AccountType = AccountType.PERSONAL
) -> Dict[str, Any]:
    """
    Ensure a user has a profile. Create one if it doesn't exist.
    
    Args:
        db: Database session
        user_id: User's UUID
        first_name: User's first name
        last_name: User's last name
        phone_number: User's phone number
        avatar_url: User's avatar URL
        account_type: User's account type
        
    Returns:
        Dict containing profile information and creation status
    """
    profile_service = ProfileService(db)
    
    # Check if profile already exists
    existing_profile = await profile_service.get_profile_by_id(user_id)
    
    if existing_profile:
        # Profile exists, return it
        profile_response = await profile_service.get_profile_response_by_id(user_id)
        return {
            "profile": profile_response,
            "created": False,
            "message": "Profile already exists"
        }
    else:
        # Create new profile
        profile_data = ProfileCreate(
            first_name=first_name or "User",
            last_name=last_name or "User",
            avatar_url=avatar_url,
            phone_number=phone_number,
            account_type=account_type
        )
        
        try:
            profile = await profile_service.create_profile(user_id, profile_data)
            return {
                "profile": profile,
                "created": True,
                "message": "Profile created successfully"
            }
        except Exception as e:
            return {
                "profile": None,
                "created": False,
                "message": f"Failed to create profile: {str(e)}",
                "error": str(e)
            }


async def create_profile_from_user_data(
    db: AsyncSession,
    user_id: UUID,
    user_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a profile from user metadata (e.g., from Supabase auth)
    
    Args:
        db: Database session
        user_id: User's UUID
        user_metadata: User metadata from auth provider
        
    Returns:
        Dict containing profile information and creation status
    """
    return await ensure_user_profile(
        db=db,
        user_id=user_id,
        first_name=user_metadata.get("first_name"),
        last_name=user_metadata.get("last_name"),
        phone_number=user_metadata.get("phone_number"),
        avatar_url=user_metadata.get("avatar_url"),
        account_type=AccountType.PERSONAL
    )


async def get_or_create_profile(
    db: AsyncSession,
    user_id: UUID,
    **profile_data
) -> Dict[str, Any]:
    """
    Get existing profile or create a new one with provided data
    
    Args:
        db: Database session
        user_id: User's UUID
        **profile_data: Profile data (first_name, last_name, etc.)
        
    Returns:
        Dict containing profile information
    """
    profile_service = ProfileService(db)
    
    # Try to get existing profile
    profile = await profile_service.get_profile_response_by_id(user_id)
    
    if profile:
        return {
            "profile": profile,
            "created": False,
            "message": "Using existing profile"
        }
    
    # Create new profile
    return await ensure_user_profile(db, user_id, **profile_data)
