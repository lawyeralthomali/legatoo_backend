from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from uuid import UUID

from ..schemas.profile import UserAuth, TokenData
from ..utils.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserAuth)
async def get_current_user_info(
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    """
    Get the current authenticated user's information from JWT token.
    This returns the user data from Supabase Auth.
    """
    return UserAuth(
        id=current_user.sub,
        email=current_user.email,
        phone=current_user.phone,
        aud=current_user.aud,
        role=current_user.role,
        created_at=str(current_user.iat),  # Convert timestamp to string
        updated_at=str(current_user.exp) if current_user.exp else None
    )


@router.get("/me/auth-status")
async def check_auth_status(
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    """
    Check if the user is authenticated and return basic auth status.
    """
    return {
        "authenticated": True,
        "user_id": str(current_user.sub),
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role
    }
