from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.logging_config import get_logger
from ..db.database import get_db
from ..schemas.request import SignupRequest, LoginRequest, RefreshTokenRequest
from ..schemas.response import ApiResponse, create_success_response, create_error_response, raise_error_response
from ..repositories.user_repository import UserRepository
from ..repositories.profile_repository import ProfileRepository
from ..services.auth_service import AuthService
from ..utils.exceptions import (
    AppException, ValidationException, ConflictException,
    AuthenticationException, ExternalServiceException
)
from ..utils.api_exceptions import ApiException
from ..interfaces.supabase_client import ISupabaseClient, SupabaseClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("supabase.env")

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


# Dependency injection functions
def get_supabase_client() -> ISupabaseClient:
    """Dependency provider for Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    print(f"Supabase URL: {supabase_url}")
    print(f"Supabase Key: {supabase_anon_key[:20]}..." if supabase_anon_key else "None")
    
    if not supabase_url or not supabase_anon_key:
        raise HTTPException(status_code=500, detail="Supabase configuration not found")
    
    return SupabaseClient(supabase_url, supabase_anon_key)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency provider for user repository."""
    return UserRepository(db)


def get_profile_repository(db: AsyncSession = Depends(get_db)) -> ProfileRepository:
    """Dependency provider for profile repository."""
    return ProfileRepository(db)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    profile_repo: ProfileRepository = Depends(get_profile_repository),
    supabase_client: ISupabaseClient = Depends(get_supabase_client)
) -> AuthService:
    """Dependency provider for authentication service."""
    return AuthService(user_repo, profile_repo, supabase_client)


@router.post("/signup", response_model=ApiResponse)
async def signup(
    signup_data: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
   
    try:
        logger.info(f"Signup request received for email: {signup_data.email}")
        # Delegate to service for business logic
        result = await auth_service.signup(signup_data)
        logger.info(f"Signup successful for email: {signup_data.email}, user ID: {result.get('user', {}).get('id')}")
        # Return success response
        return create_success_response(
            message="User and profile created successfully",
            data=result
        )
        
    except ApiException:
        # Let ApiException bubble up to global handler
        raise
        
    except ConflictException as e:
        # Handle duplicate email - return 422 Unprocessable Entity
        logger.warning(f"Signup failed - duplicate email: {signup_data.email}")
        raise_error_response(
            status_code=422,
            message=e.message,
            field=e.field
        )
        
    except ValidationException as e:
        # Handle validation errors - return 400 Bad Request
        logger.warning(f"Signup failed - validation error for email {signup_data.email}: {e.message}")
        raise_error_response(
            status_code=400,
            message=e.message,
            field=e.field
        )
        
    except ExternalServiceException as e:
        # Handle external service errors - return 500 Internal Server Error
        logger.error(f"Signup failed - external service error for email {signup_data.email}: {e.message}")
        raise_error_response(
            status_code=500,
            message=e.message,
            field=e.field
        )
        
    except Exception as e:
        # Handle unexpected errors - return 500 Internal Server Error
        logger.exception(f"Unexpected error during signup for email {signup_data.email}: {str(e)}")
        raise_error_response(
            status_code=500,
            message="Signup failed",
            field=None
        )


@router.post("/login", response_model=ApiResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Authenticate user with Supabase.
    
    Args:
        login_data: Login request data
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse with authentication data or error
    """
    try:
        logger.info(f"Login request received for email: {login_data.email}")
        # Delegate to service for business logic
        result = await auth_service.login(login_data)
        logger.info(f"Login successful for email: {login_data.email}, user ID: {result.get('user', {}).get('id')}")
        
        # Return success response
        return create_success_response(
            message="Login successful",
            data=result
        )
        
    except ApiException:
        # Let ApiException bubble up to global handler
        raise
        
    except AuthenticationException as e:
        # Handle authentication failures - return 401 Unauthorized
        raise_error_response(
            status_code=401,
            message=e.message,
            field=e.field
        )
        
    except ExternalServiceException as e:
        # Handle external service errors - return 500 Internal Server Error
        raise_error_response(
            status_code=500,
            message=e.message,
            field=e.field
        )
        
    except Exception as e:
        # Handle unexpected errors - return 500 Internal Server Error
        logger.exception(f"Unexpected error during login for email {login_data.email}: {str(e)}")
        raise_error_response(
            status_code=500,
            message="Login failed",
            field=None
        )


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:

    try:
        # Delegate to service for business logic
        result = await auth_service.refresh_token(refresh_data.refresh_token)
        
        # Return success response
        return create_success_response(
            message="Token refreshed successfully",
            data=result
        )
        
    except ApiException:
        # Let ApiException bubble up to global handler
        raise
        
    except AuthenticationException as e:
        # Handle authentication failures - return 401 Unauthorized
        raise_error_response(
            status_code=401,
            message=e.message,
            field=e.field
        )
        
    except ExternalServiceException as e:
        # Handle external service errors - return 500 Internal Server Error
        raise_error_response(
            status_code=500,
            message=e.message,
            field=e.field
        )
        
    except Exception as e:
        # Handle unexpected errors - return 500 Internal Server Error
        raise_error_response(
            status_code=500,
            message="Token refresh failed",
            field=None
        )


@router.post("/logout", response_model=ApiResponse)
async def logout(
    access_token: str,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Logout user and invalidate token.
    
    Args:
        access_token: Access token to invalidate
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse with logout status
    """
    try:
        # Delegate to service for business logic
        await auth_service.logout(access_token)
        
        # Return success response
        return create_success_response(
            message="Logout successful",
            data={"logged_out": True}
        )
        
    except ApiException:
        # Let ApiException bubble up to global handler
        raise
        
    except AuthenticationException as e:
        # Handle authentication failures - return 401 Unauthorized
        raise_error_response(
            status_code=401,
            message=e.message,
            field=e.field
        )
        
    except ExternalServiceException as e:
        # Handle external service errors - return 500 Internal Server Error
        raise_error_response(
            status_code=500,
            message=e.message,
            field=e.field
        )
        
    except Exception as e:
        # Handle unexpected errors - return 500 Internal Server Error
        raise_error_response(
            status_code=500,
            message="Logout failed",
            field=None
        )
