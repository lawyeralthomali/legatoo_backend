"""
Authentication service for business logic operations.

This module contains business logic for authentication operations using SQLite,
following the Single Responsibility Principle and Dependency Inversion.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

from ..config.logging_config import get_logger
from ..models.user import User
from ..models.profile import Profile
from ..schemas.response import raise_error_response
from ..schemas.user_schemas import UserCreate, UserLogin, UserResponse
from ..schemas.profile_schemas import ProfileCreate, ProfileResponse
from ..schemas.request import SignupRequest, LoginRequest
from ..schemas.response import create_success_response
from ..utils.exceptions import (
    ValidationException, ConflictException, AuthenticationException
)
from ..utils.api_exceptions import ApiException

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AuthService:
    """
    Authentication service for business logic operations using SQLite.
    
    This service handles all authentication-related business logic,
    including user registration, login, and profile management.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def signup(self, signup_data: SignupRequest) -> Dict[str, Any]:
        """
        Register a new user with profile.
        
        Args:
            signup_data: User registration data
            
        Returns:
            ApiResponse with user and profile information
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            # Check if user already exists
            existing_user = await self.db.execute(
                select(User).where(User.email == signup_data.email)
            )
            if existing_user.scalar_one_or_none():
                raise_error_response(
                    status_code=422,
                    message="Email already registered",
                    field="email"
                )
            
            # Create user
            hashed_password = self.get_password_hash(signup_data.password)
            user = User(
                email=signup_data.email,
                password_hash=hashed_password,
                is_active=True,
                is_verified=False
            )
            
            self.db.add(user)
            await self.db.flush()  # Get the user ID
            
            # Create profile
            profile = Profile(
                user_id=user.id,
                email=signup_data.email,
                first_name=signup_data.first_name,
                last_name=signup_data.last_name,
                phone_number=signup_data.phone_number,
                account_type=signup_data.account_type.value if signup_data.account_type else "personal"
            )
            
            self.db.add(profile)
            await self.db.commit()
            
            # Create access token
            access_token = self.create_access_token(data={"sub": str(user.id)})
            
            logger.info(f"User registered successfully: {user.email}")
            
            return create_success_response(
                message="User and profile created successfully",
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "created_at": user.created_at
                    },
                    "profile": {
                        "id": profile.id,
                        "first_name": profile.first_name,
                        "last_name": profile.last_name,
                        "phone_number": profile.phone_number,
                        "account_type": profile.account_type
                    },
                    "access_token": access_token,
                    "token_type": "bearer"
                }
            )
            
        except ApiException:
            # Re-raise ApiException as-is
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"User registration failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="User registration failed",
                field="email"
            )
    
    async def login(self, login_data: LoginRequest) -> Dict[str, Any]:
        """
        Authenticate a user.
        
        Args:
            login_data: Login credentials
            
        Returns:
            Dict containing user information and access token
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            # Find user by email
            result = await self.db.execute(
                select(User).where(User.email == login_data.email)
            )
            user = result.scalar_one_or_none()
            
            if not user or not self.verify_password(login_data.password, user.password_hash):
                raise_error_response(
                    status_code=401,
                    message="Invalid email or password",
                    field="email"
                )
            
            if not user.is_active:
                raise_error_response(
                    status_code=401,
                    message="Account is deactivated",
                    field="email"
                )
            if not user.is_verified:
                raise_error_response(
                    status_code=401,
                    message="Account is not verified, please check your email for verification",
                    field="email"
                )
            
            # Get user profile
            profile_result = await self.db.execute(
                select(Profile).where(Profile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            
            # Create access token
            access_token = self.create_access_token(data={"sub": str(user.id)})
            
            logger.info(f"User logged in successfully: {user.email}")
            
            return create_success_response(
                message="Login successful",
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "created_at": user.created_at
                    },
                    "profile": {
                        "id": profile.id if profile else None,
                        "first_name": profile.first_name if profile else None,
                        "last_name": profile.last_name if profile else None,
                        "phone_number": profile.phone_number if profile else None,
                        "account_type": profile.account_type if profile else None
                    } if profile else None,
                    "access_token": access_token,
                    "token_type": "bearer"
                }
            )
            
        except ApiException:
            # Re-raise ApiException as-is
            raise
        except Exception as e:
            logger.error(f"User login failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Login failed",
                field="email"
            )
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return await self.get_user_by_id(int(user_id))
        except JWTError:
            return None
    
    async def refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Refresh an access token.
        
        Args:
            token: Current access token
            
        Returns:
            Dict containing new access token
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            user = await self.verify_token(token)
            if not user:
                raise_error_response(
                    status_code=401,
                    message="Invalid token",
                    field="token"
                )
            
            # Create new access token
            new_token = self.create_access_token(data={"sub": str(user.id)})
            
            return create_success_response(
                message="Token refreshed successfully",
                data={
                    "access_token": new_token,
                    "token_type": "bearer"
                }
            )
            
        except ApiException:
            # Re-raise ApiException as-is
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Token refresh failed",
                field="token"
            )
    
    async def logout(self, token: str) -> Dict[str, Any]:
        """
        Logout a user (invalidate token).
        
        Args:
            token: Access token to invalidate
            
        Returns:
            Dict containing logout confirmation
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            # In a real implementation, you might want to maintain a blacklist
            # of invalidated tokens. For now, we'll just return success.
            logger.info("User logged out successfully")
            
            return create_success_response(
                message="Logout successful",
                data={"logged_out": True}
            )
            
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Logout failed",
                field="token"
            )