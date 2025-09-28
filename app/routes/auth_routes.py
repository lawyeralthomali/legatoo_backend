"""
Enhanced authentication routes with enterprise-grade security features.

This module provides comprehensive authentication endpoints including
JWT refresh token flow, brute force protection, and unified error handling.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import uuid

from ..db.database import get_db
from ..schemas.request import SignupRequest, LoginRequest, RefreshTokenRequest, ChangePasswordRequest, ResetPasswordRequest, ConfirmPasswordResetRequest
from ..schemas.response import ApiResponse
from ..services.auth_service import AuthService
from ..config.enhanced_logging import setup_logging, get_logger
from ..utils.api_exceptions import ApiException

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Setup logging
setup_logging()
logger = get_logger(__name__)


def get_auth_service(db: AsyncSession = Depends(get_db), request: Request = None) -> AuthService:
    """Dependency provider for AuthService with correlation ID."""
    correlation_id = None
    if request:
        # Try to get correlation ID from headers or generate one
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())[:8]
    
    return AuthService(db, correlation_id)


@router.post("/signup", response_model=ApiResponse)
async def signup(
    signup_data: SignupRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Register a new user with enhanced security features.
    
    Args:
        signup_data: User registration data
        request: FastAPI request object for correlation ID
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse with registration status
        
    Raises:
        HTTPException: For validation errors or duplicate email
    """
    try:
        return await auth_service.signup(signup_data)
    except ApiException:
        # Re-raise ApiException as-is (will be handled by global handler)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signup: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=ApiResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Authenticate user with enhanced security features.
    
    Args:
        login_data: Login credentials
        request: FastAPI request object for correlation ID
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse with authentication data and tokens
        
    Raises:
        HTTPException: For authentication errors
    """
    try:
        return await auth_service.login(login_data)
    except ApiException:
        # Re-raise ApiException as-is (will be handled by global handler)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Refresh authentication token using refresh token.
    
    Args:
        refresh_data: Refresh token data
        request: FastAPI request object for correlation ID
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse with new access token
        
    Raises:
        HTTPException: For invalid or expired refresh token
    """
    try:
        return await auth_service.refresh_token(refresh_data.refresh_token)
    except ApiException:
        # Re-raise ApiException as-is (will be handled by global handler)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in refresh token: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/verify-email", response_model=ApiResponse)
async def verify_email(
    verification_token: str,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Verify user email using verification token.
    
    Args:
        verification_token: Email verification token
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse with verification status
    """
    logger.info(f"Email verification request received for token: {verification_token[:10]}...")
    
    # Delegate all business logic to the service layer
    result = await auth_service.verify_email(verification_token)
    
    logger.info("Email verification successful")
    return result


@router.post("/logout", response_model=ApiResponse)
async def logout(
    refresh_data: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Logout user by revoking refresh token.
    
    Args:
        refresh_data: Refresh token data
        request: FastAPI request object for correlation ID
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse confirming logout
        
    Raises:
        HTTPException: For invalid refresh token
    """
    try:
        return await auth_service.logout(refresh_data.refresh_token)
    except ApiException:
        # Re-raise ApiException as-is (will be handled by global handler)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in logout: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/logout-all", response_model=ApiResponse)
async def logout_all_devices(
    user_id: int,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Logout user from all devices by revoking all refresh tokens.
    
    Args:
        user_id: User ID to logout from all devices
        request: FastAPI request object for correlation ID
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse confirming logout from all devices
        
    Raises:
        HTTPException: For invalid user ID
    """
    try:
        return await auth_service.logout_all_devices(user_id)
    except ApiException:
        # Re-raise ApiException as-is (will be handled by global handler)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in logout all devices: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    change_data: ChangePasswordRequest,
    user_id: int,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Change user password with current password verification.
    
    Args:
        change_data: Password change data
        user_id: User ID (from authenticated user)
        request: FastAPI request object for correlation ID
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse confirming password change
        
    Raises:
        HTTPException: For authentication or validation errors
    """
    try:
        return await auth_service.change_password(
            user_id=user_id,
            current_password=change_data.current_password,
            new_password=change_data.new_password
        )
    except ApiException:
        # Re-raise ApiException as-is (will be handled by global handler)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in change password: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/reset-password", response_model=ApiResponse)
async def request_password_reset(
    reset_data: ResetPasswordRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Request password reset by sending reset email.
    
    Args:
        reset_data: Password reset request data
        request: FastAPI request object for correlation ID
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse confirming reset request
        
    Raises:
        HTTPException: For validation errors
    """
    try:
        return await auth_service.request_password_reset(reset_data.email)
    except ApiException:
        # Re-raise ApiException as-is (will be handled by global handler)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in password reset request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/confirm-password-reset", response_model=ApiResponse)
async def confirm_password_reset(
    confirm_data: ConfirmPasswordResetRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Confirm password reset using reset token.
    
    Args:
        confirm_data: Password reset confirmation data
        request: FastAPI request object for correlation ID
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse confirming password reset
        
    Raises:
        HTTPException: For invalid or expired tokens
    """
    try:
        return await auth_service.confirm_password_reset(
            reset_token=confirm_data.reset_token,
            new_password=confirm_data.new_password
        )
    except ApiException:
        # Re-raise ApiException as-is (will be handled by global handler)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in password reset confirmation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")