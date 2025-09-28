from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID

from ..db.database import get_db
from ..schemas.profile_schemas import ProfileCreate, ProfileUpdate, ProfileResponse
from ..schemas.response import (
    ApiResponse, ErrorDetail,
    create_success_response, create_error_response
)
from ..services.profile_service import ProfileService
from ..repositories.profile_repository import ProfileRepository
from ..utils.auth import get_current_user_id, get_current_user, TokenData

router = APIRouter(prefix="/profiles", tags=["Profiles"])

# Unified Response Schemas
class ProfileGetResponse(ApiResponse):
    """Unified response for profile retrieval"""
    pass

class ProfileUpdateResponse(ApiResponse):
    """Unified response for profile updates"""
    pass

class ProfileDeleteResponse(ApiResponse):
    """Unified response for profile deletion"""
    pass


@router.get("/me", response_model=ProfileGetResponse)
async def get_current_profile(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get the current user's profile using unified response structure.
    Creates a profile if it doesn't exist.
    """
    try:
        profile_repository = ProfileRepository(db)
        profile_service = ProfileService(profile_repository)
        
        # Try to get existing profile
        profile = await profile_service.get_profile_response_by_id(current_user_id)
        
        if not profile:
            # Create a default profile if it doesn't exist
            profile = await profile_service.create_profile_if_not_exists(current_user_id)
        
        return create_success_response(
            message="Profile retrieved successfully",
            data=profile.dict()
        )
    
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve profile",
            errors=[ErrorDetail(field="profile", message=f"Internal server error: {str(e)}")]
        )


@router.post("/", response_model=ProfileUpdateResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create a new profile for the current user using unified response structure.
    """
    try:
        profile_repository = ProfileRepository(db)
        profile_service = ProfileService(profile_repository)
        profile = await profile_service.create_profile(current_user_id, profile_data)
        
        return create_success_response(
            message="Profile created successfully",
            data=profile.dict()
        )
    
    except HTTPException as e:
        if e.status_code == 409:
            return create_error_response(
                message="Profile already exists",
                errors=[ErrorDetail(field="profile", message="A profile already exists for this user")]
            )
        else:
            return create_error_response(
                message="Profile creation failed",
                errors=[ErrorDetail(field="profile", message=str(e.detail))]
            )
    except Exception as e:
        return create_error_response(
            message="Profile creation failed",
            errors=[ErrorDetail(field="profile", message=f"Internal server error: {str(e)}")]
        )


@router.put("/me", response_model=ProfileUpdateResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Update the current user's profile using unified response structure.
    """
    try:
        profile_repository = ProfileRepository(db)
        profile_service = ProfileService(profile_repository)
        
        updated_profile = await profile_service.update_profile(current_user_id, profile_update)
        
        if not updated_profile:
            return create_not_found_error_response(
                message="Profile not found",
                field="profile"
            )
        
        return create_success_response(
            message="Profile updated successfully",
            data=updated_profile.dict()
        )
    
    except Exception as e:
        return create_error_response(
            message="Profile update failed",
            errors=[ErrorDetail(field="profile", message=f"Internal server error: {str(e)}")]
        )


@router.delete("/me", response_model=ProfileDeleteResponse)
async def delete_profile(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Delete the current user's profile using unified response structure.
    """
    try:
        profile_repository = ProfileRepository(db)
        profile_service = ProfileService(profile_repository)
        
        deleted = await profile_service.delete_profile(current_user_id)
        
        if not deleted:
            return create_not_found_error_response(
                message="Profile not found",
                field="profile"
            )
        
        return create_success_response(
            message="Profile deleted successfully",
            data={"deleted": True}
        )
    
    except Exception as e:
        return create_error_response(
            message="Profile deletion failed",
            errors=[ErrorDetail(field="profile", message=f"Internal server error: {str(e)}")]
        )


@router.get("/{user_id}", response_model=ProfileGetResponse)
async def get_profile_by_id(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get a profile by user ID using unified response structure (public endpoint).
    """
    try:
        profile_repository = ProfileRepository(db)
        profile_service = ProfileService(profile_repository)
        
        profile = await profile_service.get_profile_response_by_id(user_id)
        
        if not profile:
            return create_not_found_error_response(
                message="Profile not found",
                field="user_id"
            )
        
        return create_success_response(
            message="Profile retrieved successfully",
            data=profile.dict()
        )
    
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve profile",
            errors=[ErrorDetail(field="profile", message=f"Internal server error: {str(e)}")]
        )
