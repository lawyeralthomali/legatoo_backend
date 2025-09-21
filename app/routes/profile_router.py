from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID

from ..db.database import get_db
from ..schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from ..services.profile_service import ProfileService
from ..utils.auth import get_current_user_id, get_current_user, TokenData

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/me", response_model=ProfileResponse)
async def get_current_profile(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get the current user's profile.
    Creates a profile if it doesn't exist.
    """
    profile_service = ProfileService(db)
    
    # Try to get existing profile
    profile = await profile_service.get_profile_response_by_id(current_user_id)
    
    if not profile:
        # Create a default profile if it doesn't exist
        profile = await profile_service.create_profile_if_not_exists(current_user_id)
    
    return profile


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create a new profile for the current user.
    """
    profile_service = ProfileService(db)
    return await profile_service.create_profile(current_user_id, profile_data)


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update the current user's profile.
    """
    profile_service = ProfileService(db)
    
    updated_profile = await profile_service.update_profile(current_user_id, profile_update)
    
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return updated_profile


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Delete the current user's profile.
    """
    profile_service = ProfileService(db)
    
    deleted = await profile_service.delete_profile(current_user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile_by_id(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get a profile by user ID (public endpoint).
    """
    profile_service = ProfileService(db)
    
    profile = await profile_service.get_profile_response_by_id(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile
