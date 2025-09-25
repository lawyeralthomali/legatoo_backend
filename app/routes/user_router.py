from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from uuid import UUID

from ..schemas.profile import UserAuth, TokenData
from ..utils.auth import get_current_user
from ..services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserAuth)
async def get_current_user_info(
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    """
    Get the current authenticated user's information from JWT token.
    This returns the user data from Supabase Auth.
    """
    return UserService.get_user_auth_data(current_user)


@router.get("/me/auth-status")
async def check_auth_status(
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    """
    Check if the user is authenticated and return basic auth status.
    """
    return UserService.get_auth_status_data(current_user)
