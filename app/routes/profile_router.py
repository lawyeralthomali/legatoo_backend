from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from uuid import UUID

from ..db.database import get_db
from ..schemas.profile_schemas import ProfileUpdate, ProfileResponse
from ..schemas.response import (
    ApiResponse, ErrorDetail,
    create_success_response, create_error_response, create_not_found_response,
    raise_error_response
)
from ..services.profile_service import ProfileService
from ..utils.auth import get_current_user_id, get_current_user, TokenData

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me", response_model=ApiResponse)
async def get_current_profile(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ApiResponse:
    """
    Get the current user's profile using unified response structure.
    Creates a profile if it doesn't exist.
    """
    try:
        # Service creates its own repository internally (clean architecture)
        profile_service = ProfileService(db)
        
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
        # Use raise_error_response to return proper HTTP status code
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve profile",
            field="profile",
            errors=[ErrorDetail(field="profile", message=f"Internal server error: {str(e)}")]
        )




@router.put("/me", response_model=ApiResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ApiResponse:
    """
    Update the current user's profile using unified response structure.
    Creates a profile if it doesn't exist, updates if it does.
    """
    try:
        # Service creates its own repository internally (clean architecture)
        profile_service = ProfileService(db)
        
        # Use create_or_update method that handles both cases
        updated_profile = await profile_service.create_or_update_profile(current_user_id, profile_update)
        
        return create_success_response(
            message="Profile updated successfully",
            data=updated_profile.dict()
        )
    
    except Exception as e:
        # Use raise_error_response to return proper HTTP status code
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Profile update failed",
            field="profile",
            errors=[ErrorDetail(field="profile", message=f"Internal server error: {str(e)}")]
        )




@router.get("/{user_id}", response_model=ApiResponse)
async def get_profile_by_id(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ApiResponse:
    """
    Get a profile by user ID using unified response structure (public endpoint).
    """
    try:
        # Service creates its own repository internally (clean architecture)
        profile_service = ProfileService(db)
        
        profile = await profile_service.get_profile_response_by_id(user_id)
        
        if not profile:
            # Use raise_error_response to return proper HTTP status code
            raise_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Profile not found",
                field="user_id",
                errors=[ErrorDetail(field="user_id", message="The requested profile was not found")]
            )
        
        return create_success_response(
            message="Profile retrieved successfully",
            data=profile.dict()
        )
    
    except Exception as e:
        # Use raise_error_response to return proper HTTP status code
        raise_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve profile",
            field="profile",
            errors=[ErrorDetail(field="profile", message=f"Internal server error: {str(e)}")]
        )
