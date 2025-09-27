from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.logging_config import get_logger
from ..db.database import get_db
from ..schemas.request import SignupRequest, LoginRequest, RefreshTokenRequest
from ..schemas.response import ApiResponse
from ..services.auth_service import AuthService
from ..utils.api_exceptions import ApiException

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(db)


@router.post("/signup", response_model=ApiResponse)
async def signup(
    signup_data: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Register a new user.
    
    Args:
        signup_data: User registration data
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse with user data or error
    """
    logger.info(f"Signup request received for email: {signup_data.email}")
    
    # Delegate all business logic to the service layer
    result = await auth_service.signup(signup_data)
    
    logger.info(f"Signup successful for email: {signup_data.email}")
    return result


@router.post("/login", response_model=ApiResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Authenticate user.
    
    Args:
        login_data: Login credentials
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse with authentication data or error
    """
    logger.info(f"Login request received for email: {login_data.email}")
    
    # Delegate all business logic to the service layer
    result = await auth_service.login(login_data)
    
    logger.info(f"Login successful for email: {login_data.email}")
    return result


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """
    Refresh authentication token.
    
    Args:
        refresh_data: Refresh token data
        auth_service: Authentication service (injected)
        
    Returns:
        ApiResponse with new token or error
    """
    # Delegate all business logic to the service layer
    result = await auth_service.refresh_token(refresh_data.refresh_token)
    return result


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
    # Delegate all business logic to the service layer
    result = await auth_service.logout(access_token)
    return result
