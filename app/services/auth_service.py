"""
Authentication service for business logic operations.

This module contains business logic for authentication operations,
following the Single Responsibility Principle and Dependency Inversion.
"""

from typing import Optional, Dict, Any
from uuid import UUID
import logging

from fastapi import HTTPException

from ..repositories.user_repository import IUserRepository
from ..repositories.profile_repository import IProfileRepository
from ..schemas.request import SignupRequest, LoginRequest
from ..schemas.user import UserResponse
from ..schemas.profile import ProfileResponse
from ..interfaces.supabase_client import ISupabaseClient
from ..utils.exceptions import (
    ValidationException, ConflictException, ExternalServiceException
)

logger = logging.getLogger(__name__)


class AuthService:
  
    
    def __init__(
        self,
        user_repository: IUserRepository,
        profile_repository: IProfileRepository,
        supabase_client: ISupabaseClient
    ):
       
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.supabase_client = supabase_client
    
    async def signup(self, signup_data: SignupRequest) -> Dict[str, Any]:

        try:
            # 1. Create user in Supabase Auth (this will fail if email already exists)
            try:
                user_data = await self.supabase_client.signup(
                    email=signup_data.email,
                    password=signup_data.password,
                    data={
                        "first_name": signup_data.first_name,
                        "last_name": signup_data.last_name,
                        "phone_number": signup_data.phone_number
                    }
                )
                print(f"i am here after signup: {user_data}")
            except HTTPException as e:
                logger.error(f"Supabase signup failed: {str(e)}")
                
                # Check if it's a duplicate email error from Supabase
                error_str = str(e.detail).lower()
                if ("already registered" in error_str or 
                    "user already registered" in error_str or 
                    "email already exists" in error_str or
                    "user already exists" in error_str or
                    "duplicate" in error_str):
                    raise ConflictException(
                        message="Email already registered",
                        field="email"
                    )
                else:
                    raise ExternalServiceException(
                        message="User creation failed",
                        field="email",
                        service="Supabase",
                        details={"error": str(e.detail)}
                    )
            except Exception as e:
                logger.error(f"Supabase signup failed: {str(e)}")
                
                # Check if it's a duplicate email error from Supabase
                error_str = str(e).lower()
                if ("already registered" in error_str or 
                    "user already registered" in error_str or 
                    "email already exists" in error_str or
                    "user already exists" in error_str or
                    "duplicate" in error_str):
                    raise ConflictException(
                        message="Email already registered",
                        field="email"
                    )
                else:
                    raise ExternalServiceException(
                        message="User creation failed",
                        field="email",
                        service="Supabase",
                        details={"error": str(e)}
                    )
            
            # 3. Validate user creation response
            user_id = user_data.get("id")
            if not user_id:
                raise ExternalServiceException(
                    message="User creation failed",
                    field="user",
                    service="Supabase",
                    details={"error": "No user ID returned"}
                )
            
            # 4. Only create profile if user was successfully created in Supabase
            try:
                profile_data = {
                    "email": signup_data.email,
                    "first_name": signup_data.first_name or "User",
                    "last_name": signup_data.last_name or "User",
                    "phone_number": signup_data.phone_number,
                    "account_type": "personal"
                }
                
                profile = await self.profile_repository.create_profile(
                    user_id=UUID(user_id),
                    profile_data=profile_data
                )
                
            except Exception as e:
                logger.error(f"Profile creation failed for user {user_id}: {str(e)}")
                
                # Check if it's a unique constraint violation (profile already exists)
                error_str = str(e).lower()
                if "unique constraint" in error_str or "duplicate key" in error_str or "already exists" in error_str:
                    # This means the user already exists in Supabase but we're trying to create a profile
                    # Map this to an email already registered error
                    raise ConflictException(
                        message="Email already registered",
                        field="email"
                    )
                else:
                    raise ExternalServiceException(
                        message="Profile creation failed",
                        field="profile",
                        service="Database",
                        details={"error": str(e)}
                    )
            
            # 5. Return success data
            return {
                "user": {
                    "id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "created_at": user_data.get("created_at"),
                    "first_name": signup_data.first_name,
                    "last_name": signup_data.last_name,
                    "phone_number": signup_data.phone_number
                },
                "profile": {
                    "id": profile.id,  # Same as Supabase user_id
                    "email": profile.email,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "phone_number": profile.phone_number,
                    "account_type": profile.account_type,
                    "created_at": profile.created_at
                }
            }
            
        except (ValidationException, ConflictException, ExternalServiceException):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error during signup: {str(e)}")
            raise ExternalServiceException(
                message="Signup failed",
                field="general",
                service="AuthService",
                details={"error": str(e)}
            )
    
    async def login(self, login_data: LoginRequest) -> Dict[str, Any]:
        """
        Authenticate user and return session data.
        
        Args:
            login_data: Login request data
            
        Returns:
            Dict containing user and session data
            
        Raises:
            ValidationException: For validation errors
            AuthenticationException: For authentication failures
            ExternalServiceException: For auth service errors
        """
        try:
            # Authenticate with Supabase
            session_data = await self.supabase_client.login(
                email=login_data.email,
                password=login_data.password
            )
            
            # Get user data
            user_id = session_data.get("user", {}).get("id")
            if not user_id:
                raise ExternalServiceException(
                    message="Authentication failed",
                    field="email",
                    service="Supabase",
                    details={"error": "No user ID in session"}
                )
            
            # Get profile data
            try:
                profile = await self.profile_repository.get_profile_by_user_id(UUID(user_id))
            except Exception as e:
                logger.warning(f"Could not fetch profile for user {user_id}: {str(e)}")
                profile = None
            
            return {
                "user": {
                    "id": user_id,
                    "email": session_data.get("user", {}).get("email"),
                    "first_name": profile.first_name if profile else None,
                    "last_name": profile.last_name if profile else None,
                    "phone_number": profile.phone_number if profile else None
                },
                "session": {
                    "access_token": session_data.get("access_token"),
                    "refresh_token": session_data.get("refresh_token"),
                    "expires_at": session_data.get("expires_at")
                },
                "profile": {
                    "id": profile.id,  # Same as Supabase user_id
                    "email": profile.email,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "phone_number": profile.phone_number,
                    "account_type": profile.account_type,
                    "created_at": profile.created_at
                } if profile else None
            }
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise ExternalServiceException(
                message="Authentication failed",
                field="email",
                service="Supabase",
                details={"error": str(e)}
            )
