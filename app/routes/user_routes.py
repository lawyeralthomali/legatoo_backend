"""
User routes with clean architecture principles.

This module provides thin route handlers for user-related operations
that delegate to services and return unified API responses.
"""

from typing import List, Dict, Any, Union
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..services.user_management.user_service import UserService
from ..utils.exceptions import (
    NotFoundException, ValidationException, AppException
)
from ..utils.auth import get_current_user_id, get_current_user
from ..schemas.profile_schemas import TokenData

router = APIRouter(prefix="/users", tags=["Users"])


# Dependency injection function - Only inject service, not repositories
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Dependency provider for user service.
    
    Following clean architecture: Routes depend only on Services.
    Services handle their own repository dependencies internally.
    """
    return UserService(db)


@router.get("/{user_id}", response_model=ApiResponse)
async def get_user(
    user_id: Union[UUID, int] = Path(..., description="User ID"),
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        user_service: User service (injected)
        
    Returns:
        ApiResponse with user data or error
    """
    try:
        # Delegate to service for business logic
        user = await user_service.get_user_by_id(user_id)
        
        # Return success response
        return create_success_response(
            message="User retrieved successfully",
            data=user.dict()
        )
        
    except NotFoundException as e:
        # Handle not found errors
        return create_error_response(
            message=e.message,
            errors=[{"field": e.field, "message": e.message}]
        )
        
    except Exception as e:
        # Handle unexpected errors
        return create_error_response(
            message="Failed to retrieve user",
            errors=[{"field": None, "message": "An unexpected error occurred"}]
        )


@router.get("/", response_model=ApiResponse)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """
    Get all users with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        user_service: User service (injected)
        
    Returns:
        ApiResponse with users data or error
    """
    try:
        # Delegate to service for business logic
        users = await user_service.get_all_users(skip=skip, limit=limit)
        
        # Return success response
        return create_success_response(
            message="Users retrieved successfully",
            data={
                "users": [user.dict() for user in users],
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "count": len(users)
                }
            }
        )
        
    except ValidationException as e:
        # Handle validation errors
        return create_error_response(
            message=e.message,
            errors=[{"field": e.field, "message": e.message}]
        )
        
    except Exception as e:
        # Handle unexpected errors
        return create_error_response(
            message="Failed to retrieve users",
            errors=[{"field": None, "message": "An unexpected error occurred"}]
        )


@router.get("/search", response_model=ApiResponse)
async def search_users(
    query: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """
    Search users by query.
    
    Args:
        query: Search query
        skip: Number of records to skip
        limit: Maximum number of records to return
        user_service: User service (injected)
        
    Returns:
        ApiResponse with search results or error
    """
    try:
        # Delegate to service for business logic
        users = await user_service.search_users(query=query, skip=skip, limit=limit)
        
        # Return success response
        return create_success_response(
            message="Search completed successfully",
            data={
                "users": [user.dict() for user in users],
                "query": query,
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "count": len(users)
                }
            }
        )
        
    except ValidationException as e:
        # Handle validation errors
        return create_error_response(
            message=e.message,
            errors=[{"field": e.field, "message": e.message}]
        )
        
    except Exception as e:
        # Handle unexpected errors
        return create_error_response(
            message="Search failed",
            errors=[{"field": None, "message": "An unexpected error occurred"}]
        )


@router.get("/{user_id}/profile", response_model=ApiResponse)
async def get_user_profile(
    user_id: Union[UUID, int] = Path(..., description="User ID"),
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """
    Get user's profile.
    
    Args:
        user_id: User ID
        user_service: User service (injected)
        
    Returns:
        ApiResponse with profile data or error
    """
    try:
        # Delegate to service for business logic
        profile = await user_service.get_user_profile(user_id)
        
        # Return success response
        return create_success_response(
            message="Profile retrieved successfully",
            data=profile.dict()
        )
        
    except NotFoundException as e:
        # Handle not found errors
        return create_error_response(
            message=e.message,
            errors=[{"field": e.field, "message": e.message}]
        )
        
    except Exception as e:
        # Handle unexpected errors
        return create_error_response(
            message="Failed to retrieve profile",
            errors=[{"field": None, "message": "An unexpected error occurred"}]
        )


@router.get("/{user_id}/complete", response_model=ApiResponse)
async def get_user_complete(
    user_id: Union[UUID, int] = Path(..., description="User ID"),
    current_user_id: Union[UUID, int] = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
) -> ApiResponse:
    """
    Get user with their profile in a single response.
    
    Args:
        user_id: User ID
        user_service: User service (injected)
        
    Returns:
        ApiResponse with user and profile data or error
    """
    try:
        # Delegate to service for business logic
        result = await user_service.get_user_with_profile(user_id)
        
        # Return success response
        return create_success_response(
            message="User and profile retrieved successfully",
            data=result
        )
        
    except NotFoundException as e:
        # Handle not found errors
        return create_error_response(
            message=e.message,
            errors=[{"field": e.field, "message": e.message}]
        )
        
    except Exception as e:
        # Handle unexpected errors
        return create_error_response(
            message="Failed to retrieve user data",
            errors=[{"field": None, "message": "An unexpected error occurred"}]
        )
