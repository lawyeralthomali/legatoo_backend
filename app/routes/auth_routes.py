from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..schemas.request import SignupRequest, LoginRequest, RefreshTokenRequest
from ..schemas.response import ApiResponse, create_success_response, create_error_response
from ..repositories.user_repository import UserRepository
from ..repositories.profile_repository import ProfileRepository
from ..services.auth_service import AuthService
from ..utils.exceptions import (
    AppException, ValidationException, ConflictException,
    AuthenticationException, ExternalServiceException
)
from ..interfaces.supabase_client import ISupabaseClient, SupabaseClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("supabase.env")

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
        # Delegate to service for business logic
        result = await auth_service.signup(signup_data)
        print(f"hi iam here after signup auth_routes.py: {result}")
        # Return success response
        return create_success_response(
            message="User and profile created successfully",
            data=result
        )
        
    except ConflictException as e:
        # Handle duplicate email
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message=e.message,
            errors=[ErrorDetail(field=e.field, message=e.message)]
        )
        
    except ValidationException as e:
        # Handle validation errors
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message=e.message,
            errors=[ErrorDetail(field=e.field, message=e.message)]
        )
        
    except ExternalServiceException as e:
        # Handle external service errors
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message=e.message,
            errors=[ErrorDetail(field=e.field, message=e.message)]
        )
        
    except Exception as e:
        # Handle unexpected errors
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message="Signup failed",
            errors=[ErrorDetail(field=None, message="An unexpected error occurred")]
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
        # Delegate to service for business logic
        result = await auth_service.login(login_data)
        
        # Return success response
        return create_success_response(
            message="Login successful",
            data=result
        )
        
    except AuthenticationException as e:
        # Handle authentication failures
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message=e.message,
            errors=[ErrorDetail(field=e.field, message=e.message)]
        )
        
    except ExternalServiceException as e:
        # Handle external service errors
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message=e.message,
            errors=[ErrorDetail(field=e.field, message=e.message)]
        )
        
    except Exception as e:
        # Handle unexpected errors
        return create_error_response(
            message="Login failed",
            errors=[{"field": None, "message": "An unexpected error occurred"}]
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
        
    except AuthenticationException as e:
        # Handle authentication failures
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message=e.message,
            errors=[ErrorDetail(field=e.field, message=e.message)]
        )
        
    except ExternalServiceException as e:
        # Handle external service errors
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message=e.message,
            errors=[ErrorDetail(field=e.field, message=e.message)]
        )
        
    except Exception as e:
        # Handle unexpected errors
        return create_error_response(
            message="Token refresh failed",
            errors=[{"field": None, "message": "An unexpected error occurred"}]
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
        
    except AuthenticationException as e:
        # Handle authentication failures
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message=e.message,
            errors=[ErrorDetail(field=e.field, message=e.message)]
        )
        
    except ExternalServiceException as e:
        # Handle external service errors
        from ..schemas.response import ErrorDetail
        return create_error_response(
            message=e.message,
            errors=[ErrorDetail(field=e.field, message=e.message)]
        )
        
    except Exception as e:
        # Handle unexpected errors
        return create_error_response(
            message="Logout failed",
            errors=[{"field": None, "message": "An unexpected error occurred"}]
        )
