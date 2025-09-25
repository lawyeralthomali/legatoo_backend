"""
User service
Handles business logic for user-related operations
"""
from typing import Dict, Any
from uuid import UUID

from ..utils.auth import TokenData
from ..schemas.profile import UserAuth


class UserService:
    """Service for handling user business logic"""
    
    @staticmethod
    def get_user_auth_data(current_user: TokenData) -> UserAuth:
        """Get user authentication data formatted for API response"""
        return UserAuth(
            id=current_user.sub,
            email=current_user.email,
            phone=current_user.phone,
            aud=current_user.aud,
            role=current_user.role,
            created_at=str(current_user.iat),  # Convert timestamp to string
            updated_at=str(current_user.exp) if current_user.exp else None
        )
    
    @staticmethod
    def get_auth_status_data(current_user: TokenData) -> Dict[str, Any]:
        """Get authentication status data"""
        return {
            "authenticated": True,
            "user_id": str(current_user.sub),
            "email": current_user.email,
            "phone": current_user.phone,
            "role": current_user.role
        }
