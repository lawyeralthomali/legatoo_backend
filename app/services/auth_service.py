"""
Authentication service for business logic operations.

This module contains business logic for authentication operations,
following the Single Responsibility Principle and Dependency Inversion.
"""

from typing import Dict, Any
from uuid import UUID

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from ..config.logging_config import get_logger

from ..repositories.user_repository import IUserRepository
from ..repositories.profile_repository import IProfileRepository
from ..schemas.request import SignupRequest, LoginRequest
from ..interfaces.supabase_client import ISupabaseClient
from ..utils.exceptions import (
    ValidationException, ConflictException, ExternalServiceException
)

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service for business logic operations.
    
    This service handles user authentication, registration, and profile management
    using Supabase Auth and the application's database repositories.
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        profile_repository: IProfileRepository,
        supabase_client: ISupabaseClient
    ):
        """
        Initialize the authentication service.
        
        Args:
            user_repository: Repository for user data operations
            profile_repository: Repository for profile data operations
            supabase_client: Client for Supabase authentication operations
        """
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.supabase_client = supabase_client
    
    async def signup(self, signup_data: SignupRequest) -> Dict[str, Any]:
        """
        Register a new user with Supabase Auth and create their profile.
        
        Args:
            signup_data: User registration data
            
        Returns:
            Dict containing user and profile information
            
        Raises:
            ConflictException: If email is already registered
            ExternalServiceException: For service errors
        """
        try:
            # 1. Create user in Supabase Auth (async-safe)
            try:
                user_data = await run_in_threadpool(
                    self.supabase_client.signup,
                    signup_data.email,
                    signup_data.password,
                    {
                        "first_name": signup_data.first_name,
                        "last_name": signup_data.last_name,
                        "phone_number": signup_data.phone_number
                    }
                )
                logger.info(f"Supabase signup successful for user: {user_data.get('email')}")
            except HTTPException as e:
                # Log the HTTP exception with full context
                logger.exception(f"Supabase signup failed for email {signup_data.email}: {e.detail}")
                
                # SupabaseClient already handles error mapping, just propagate
                if e.status_code == 422:
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
            
            # 2. Validate user creation response
            user_id = user_data.get("id")
            if not user_id:
                logger.error(f"Supabase signup succeeded but no user ID returned for email {signup_data.email}")
                raise ExternalServiceException(
                    message="User creation failed",
                    field="user",
                    service="Supabase",
                    details={"error": "No user ID returned"}
                )
            
            # 3. Create profile for the new user
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
                logger.exception(f"Profile creation failed for user {user_id} (email: {signup_data.email}): {str(e)}")
                
                # Check if it's a unique constraint violation (profile already exists)
                error_str = str(e).lower()
                if "unique constraint" in error_str or "duplicate key" in error_str or "already exists" in error_str:
                    # This means the user already exists in Supabase but we're trying to create a profile
                    # Map this to an email already registered error
                    logger.warning(f"Profile already exists for user {user_id} (email: {signup_data.email})")
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
            
            # 4. Return success data
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
            # Re-raise our custom exceptions (they're already logged by their handlers)
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during signup for email {signup_data.email}: {str(e)}")
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
            # Authenticate with Supabase (async-safe)
            session_data = await run_in_threadpool(
                self.supabase_client.login,
                login_data.email,
                login_data.password
            )
            
            # Get user data
            user_id = session_data.get("user", {}).get("id")
            if not user_id:
                logger.error(f"Supabase login succeeded but no user ID in session for email {login_data.email}")
                raise ExternalServiceException(
                    message="Authentication failed",
                    field="email",
                    service="Supabase",
                    details={"error": "No user ID in session"}
                )
            
            # Get profile data
            try:
                profile = await self.profile_repository.get_profile_by_user_id(UUID(user_id))
                logger.info(f"Profile fetched successfully for user {user_id}")
            except Exception as e:
                logger.warning(f"Could not fetch profile for user {user_id} (email: {login_data.email}): {str(e)}")
                profile = None
            
            # Build response data
            response_data = {
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
                }
            }
            
            # Add profile data if it exists
            if profile:
                response_data["profile"] = {
                    "id": profile.id,  # Same as Supabase user_id
                    "email": profile.email,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "phone_number": profile.phone_number,
                    "account_type": profile.account_type,
                    "created_at": profile.created_at
                }
            else:
                response_data["profile"] = None
            
            return response_data
            
        except HTTPException as e:
            # Log the HTTP exception with full context
            logger.exception(f"Supabase login failed for email {login_data.email}: {e.detail}")
            
            # Handle authentication errors from Supabase client
            if e.status_code == 401:
                raise ExternalServiceException(
                    message="Invalid email or password",
                    field="email",
                    service="Supabase",
                    details={"error": str(e.detail)}
                )
            else:
                raise ExternalServiceException(
                    message="Authentication failed",
                    field="email",
                    service="Supabase",
                    details={"error": str(e.detail)}
                )
        except Exception as e:
            logger.exception(f"Unexpected error during login for email {login_data.email}: {str(e)}")
            raise ExternalServiceException(
                message="Authentication failed",
                field="email",
                service="Supabase",
                details={"error": str(e)}
            )
    
    async def check_user_exists(self, email: str) -> bool:
        """
        Check if a user exists in the profiles table.
        
        Args:
            email: Email address to check
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            result = await run_in_threadpool(
                self.supabase_client.check_user_exists,
                email
            )
            logger.info(f"User existence check completed for email {email}: {result}")
            return result
        except Exception as e:
            logger.warning(f"Could not check if user exists for email {email}: {str(e)}")
            return False
