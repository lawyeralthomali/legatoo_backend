"""
Enhanced authentication service for enterprise-grade security.

This module contains comprehensive authentication business logic including
JWT refresh token flow, brute force protection, email verification retry,
and unified error handling following enterprise security standards.
"""

from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import secrets
import string
import hashlib

from ..config.enhanced_logging import get_logger, log_auth_attempt, log_security_event, mask_email
from ..models.user import User
from ..models.profile import Profile
from ..models.refresh_token import RefreshToken
from ..models.role import DEFAULT_USER_ROLE
from ..schemas.response import raise_error_response, create_success_response
from ..schemas.request import SignupRequest, LoginRequest
from ..services.email_service import EmailService
from ..utils.api_exceptions import ApiException

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 30 seconds for testing token expiration
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Long-lived refresh tokens

# Security settings
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class AuthService:
    """
    Enhanced authentication service with enterprise-grade security features.
    
    This service handles comprehensive authentication including:
    - JWT access/refresh token flow
    - Brute force protection
    - Email verification with retry
    - Unified error handling
    - Security logging
    """
    
    def __init__(self, db: AsyncSession, correlation_id: Optional[str] = None):
        self.db = db
        self.email_service = EmailService()
        self.correlation_id = correlation_id
        self.logger = get_logger(__name__, correlation_id)
    
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
    
    def generate_refresh_token(self) -> str:
        """Generate a secure refresh token."""
        return secrets.token_urlsafe(32)
    
    def hash_refresh_token(self, token: str) -> str:
        """Hash refresh token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def create_refresh_token_record(self, user_id: int, token: str) -> RefreshToken:
        """Create a refresh token record in the database."""
        token_hash = self.hash_refresh_token(token)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        refresh_token = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            is_active=True
        )
        
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        
        return refresh_token
    
    async def validate_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Validate refresh token and return the record if valid."""
        token_hash = self.hash_refresh_token(token)
        
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.is_active == True,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            )
        )
        
        refresh_token = result.scalar_one_or_none()
        
        if refresh_token:
            # Update last used timestamp
            refresh_token.last_used_at = datetime.utcnow()
            await self.db.commit()
        
        return refresh_token
    
    async def revoke_refresh_token(self, token: str) -> bool:
        """Revoke a refresh token."""
        token_hash = self.hash_refresh_token(token)
        
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        
        refresh_token = result.scalar_one_or_none()
        if refresh_token:
            refresh_token.is_active = False
            await self.db.commit()
            return True
        
        return False
    
    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user."""
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_active == True
                )
            )
        )
        
        tokens = result.scalars().all()
        count = 0
        
        for token in tokens:
            token.is_active = False
            count += 1
        
        await self.db.commit()
        return count
    
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
                self.logger.warning(f"Signup attempt with existing email: {mask_email(signup_data.email)}")
                raise_error_response(
                    status_code=422,
                    message="Email already registered",
                    field="email"
                )
            
            # Check for duplicate phone number if provided
            if signup_data.phone_number:
                existing_phone = await self.db.execute(
                    select(Profile).where(Profile.phone_number == signup_data.phone_number)
                )
                if existing_phone.scalar_one_or_none():
                    self.logger.warning(f"Signup attempt with existing phone number: {signup_data.phone_number}")
                    log_security_event(
                        self.logger,
                        "Duplicate phone number signup attempt",
                        email=mask_email(signup_data.email),
                        phone_number=signup_data.phone_number,
                        correlation_id=self.correlation_id
                    )
                    raise_error_response(
                        status_code=422,
                        message="Phone number is already registered",
                        field="phone_number"
                    )
            
            # Create user with verification token
            hashed_password = self.get_password_hash(signup_data.password)
            verification_token = self.email_service.generate_verification_token()
            verification_expires = datetime.utcnow() + timedelta(hours=24)  # 24 hours expiry
            
            user = User(
                email=signup_data.email,
                password_hash=hashed_password,
                is_active=True,
                is_verified=False,
                verification_token=verification_token,
                verification_token_expires=verification_expires,
                failed_attempts=0,
                email_sent=False,
                role=DEFAULT_USER_ROLE  # Set default admin role for new signups
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
            
            # Send verification email with retry logic
            email_sent = False
            try:
                user_name = f"{signup_data.first_name} {signup_data.last_name}"
                email_sent = await self.email_service.send_verification_email(
                    to_email=signup_data.email,
                    user_name=user_name,
                    verification_token=verification_token
                )
                
                if email_sent:
                    user.email_sent = True
                    user.email_sent_at = datetime.utcnow()
                    await self.db.commit()
                    self.logger.info(f"Verification email sent successfully to {mask_email(signup_data.email)}")
                else:
                    self.logger.warning(f"Email service not configured, verification email not sent to {mask_email(signup_data.email)}")
                    
            except Exception as e:
                self.logger.error(f"Failed to send verification email to {mask_email(signup_data.email)}: {str(e)}")
                # Mark email as not sent for retry mechanism
                user.email_sent = False
                await self.db.commit()
            
            self.logger.info(f"User registered successfully: {mask_email(user.email)}")
            
            return create_success_response(
                message="User registered successfully. Please check your email for verification instructions.",
                data={
                    "email": user.email,
                    "verification_required": True,
                    "email_sent": email_sent,
                    "message": "A verification email has been sent to your email address. Please check your inbox and click the verification link to activate your account." if email_sent else "Account created successfully. Email verification will be sent shortly."
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
            
            # Check if user exists
            if not user:
                log_auth_attempt(self.logger, login_data.email, False, self.correlation_id, 
                               reason="user_not_found")
                raise_error_response(
                    status_code=401,
                    message="Invalid email or password",
                    field="email"
                )
            
            # Check if account is locked due to brute force attempts
            if user.locked_until and user.locked_until > datetime.utcnow():
                remaining_time = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
                log_security_event(self.logger, "account_locked", self.correlation_id,
                                 email=mask_email(user.email), remaining_minutes=remaining_time)
                raise_error_response(
                    status_code=429,
                    message=f"Account is temporarily locked due to multiple failed attempts. Try again in {remaining_time} minutes.",
                    field="email"
                )
            
            # Verify password
            if not self.verify_password(login_data.password, user.password_hash):
                # Increment failed attempts
                user.failed_attempts += 1
                
                # Lock account if max attempts reached
                if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                    log_security_event(self.logger, "account_locked_brute_force", self.correlation_id,
                                     email=mask_email(user.email), failed_attempts=user.failed_attempts)
                
                await self.db.commit()
                
                log_auth_attempt(self.logger, login_data.email, False, self.correlation_id,
                               reason="invalid_password", failed_attempts=user.failed_attempts)
                
                raise_error_response(
                    status_code=401,
                    message="Invalid email or password",
                    field="email"
                )
            
            # Check if account is active
            if not user.is_active:
                log_auth_attempt(self.logger, login_data.email, False, self.correlation_id,
                               reason="account_deactivated")
                raise_error_response(
                    status_code=401,
                    message="Account is deactivated",
                    field="email"
                )
            
            # Check if email is verified
            if not user.is_verified:
                log_auth_attempt(self.logger, login_data.email, False, self.correlation_id,
                               reason="email_not_verified")
                raise_error_response(
                    status_code=401,
                    message="Account is not verified, please check your email for verification",
                    field="email"
                )
            
            # Reset failed attempts on successful login
            user.failed_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            await self.db.commit()
            
            # Get user profile
            profile_result = await self.db.execute(
                select(Profile).where(Profile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            
            # Generate tokens
            access_token = self.create_access_token(data={
                "sub": str(user.id), 
                "email": user.email,
                "role": user.role  # Include user role in JWT token
            })
            refresh_token = self.generate_refresh_token()
            
            # Store refresh token
            await self.create_refresh_token_record(user.id, refresh_token)
            
            log_auth_attempt(self.logger, login_data.email, True, self.correlation_id,
                           user_id=user.id)
            
            return create_success_response(
                message="Login successful",
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "is_active": user.is_active,
                        "is_verified": user.is_verified,
                        "role": user.role,  # Include user role in response
                        "last_login": user.last_login
                    },
                    "profile": {
                        "id": profile.id if profile else None,
                        "first_name": profile.first_name if profile else None,
                        "last_name": profile.last_name if profile else None,
                        "phone_number": profile.phone_number if profile else None,
                        "account_type": profile.account_type if profile else None
                    } if profile else None,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
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
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token using a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            ApiResponse with new access token
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            # Validate refresh token
            refresh_token_record = await self.validate_refresh_token(refresh_token)
            if not refresh_token_record:
                self.logger.warning(f"Invalid refresh token attempt: {refresh_token[:10]}...")
                raise_error_response(
                    status_code=401,
                    message="Invalid or expired refresh token",
                    field="refresh_token"
                )
            
            # Get user
            user = await self.get_user_by_id(refresh_token_record.user_id)
            if not user or not user.is_active:
                self.logger.warning(f"Refresh token for inactive user: {refresh_token_record.user_id}")
                raise_error_response(
                    status_code=401,
                    message="User account is inactive",
                    field="refresh_token"
                )
            
            # Generate new access token
            access_token = self.create_access_token(data={
                "sub": str(user.id), 
                "email": user.email,
                "role": user.role  # Include user role in JWT token
            })
            
            self.logger.info(f"Token refreshed successfully for user: {mask_email(user.email)}")
            
            return create_success_response(
                message="Token refreshed successfully",
                data={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
                }
            )
            
        except ApiException:
            # Re-raise ApiException as-is
            raise
        except Exception as e:
            self.logger.error(f"Token refresh failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Token refresh failed",
                field="refresh_token"
            )
    
    async def logout(self, refresh_token: str) -> Dict[str, Any]:
        """
        Logout user by revoking refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            ApiResponse confirming logout
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            # Revoke refresh token
            revoked = await self.revoke_refresh_token(refresh_token)
            
            if revoked:
                self.logger.info("User logged out successfully")
                return create_success_response(
                    message="Logged out successfully",
                    data={"logout": True}
                )
            else:
                self.logger.warning("Logout attempt with invalid refresh token")
                raise_error_response(
                    status_code=401,
                    message="Invalid refresh token",
                    field="refresh_token"
                )
                
        except ApiException:
            # Re-raise ApiException as-is
            raise
        except Exception as e:
            self.logger.error(f"Logout failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Logout failed",
                field="refresh_token"
            )
    
    async def logout_all_devices(self, user_id: int) -> Dict[str, Any]:
        """
        Logout user from all devices by revoking all refresh tokens.
        
        Args:
            user_id: User ID to logout from all devices
            
        Returns:
            ApiResponse confirming logout from all devices
        """
        try:
            count = await self.revoke_all_user_tokens(user_id)
            
            self.logger.info(f"User {user_id} logged out from all devices ({count} tokens revoked)")
            
            return create_success_response(
                message="Logged out from all devices successfully",
                data={"revoked_tokens": count}
            )
            
        except Exception as e:
            self.logger.error(f"Logout all devices failed for user {user_id}: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Logout from all devices failed",
                field="user_id"
            )
    
    async def change_password(self, user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change user password with current password verification.
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            ApiResponse confirming password change
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            # Get user
            user = await self.get_user_by_id(user_id)
            if not user:
                self.logger.warning(f"Password change attempt for non-existent user: {user_id}")
                raise_error_response(
                    status_code=404,
                    message="User not found",
                    field="user_id"
                )
            
            # Verify current password
            if not self.verify_password(current_password, user.password_hash):
                self.logger.warning(f"Password change failed - incorrect current password for user: {mask_email(user.email)}")
                raise_error_response(
                    status_code=401,
                    message="Current password is incorrect",
                    field="current_password"
                )
            
            # Check if new password is different from current
            if self.verify_password(new_password, user.password_hash):
                self.logger.warning(f"Password change failed - new password same as current for user: {mask_email(user.email)}")
                raise_error_response(
                    status_code=400,
                    message="New password must be different from current password",
                    field="new_password"
                )
            
            # Update password
            user.password_hash = self.get_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            
            # Revoke all refresh tokens for security
            revoked_count = await self.revoke_all_user_tokens(user_id)
            
            await self.db.commit()
            
            self.logger.info(f"Password changed successfully for user: {mask_email(user.email)}")
            
            return create_success_response(
                message="Password changed successfully",
                data={
                    "password_changed": True,
                    "tokens_revoked": revoked_count,
                    "message": "Your password has been changed successfully. Please log in again with your new password."
                }
            )
            
        except ApiException:
            # Re-raise ApiException as-is
            raise
        except Exception as e:
            self.logger.error(f"Password change failed for user {user_id}: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Password change failed",
                field="password"
            )
    
    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request password reset by sending reset email.
        
        Args:
            email: User's email address
            
        Returns:
            ApiResponse confirming reset request
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            # Find user by email
            user = await self.get_user_by_email(email)
            if not user:
                # Don't reveal if email exists or not for security
                self.logger.info(f"Password reset requested for non-existent email: {mask_email(email)}")
                return create_success_response(
                    message="If the email exists, a password reset link has been sent",
                    data={
                        "reset_requested": True,
                        "message": "If an account with this email exists, you will receive a password reset link shortly."
                    }
                )
            
            # Check if user is active
            if not user.is_active:
                self.logger.warning(f"Password reset requested for inactive user: {mask_email(email)}")
                return create_success_response(
                    message="If the email exists, a password reset link has been sent",
                    data={
                        "reset_requested": True,
                        "message": "If an account with this email exists, you will receive a password reset link shortly."
                    }
                )
            
            # Generate reset token
            reset_token = self.email_service.generate_verification_token()
            reset_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
            
            # Update user with reset token
            user.password_reset_token = reset_token
            user.password_reset_token_expires = reset_expires
            await self.db.commit()
            
            # Send reset email
            email_sent = False
            try:
                user_name = f"{user.email.split('@')[0]}"  # Use email prefix as name
                email_sent = await self.email_service.send_password_reset_email(
                    to_email=user.email,
                    user_name=user_name,
                    reset_token=reset_token
                )
                
                if email_sent:
                    self.logger.info(f"Password reset email sent successfully to {mask_email(user.email)}")
                else:
                    self.logger.warning(f"Password reset email not sent to {mask_email(user.email)} - SMTP not configured")
                    
            except Exception as e:
                self.logger.error(f"Failed to send password reset email to {mask_email(user.email)}: {str(e)}")
            
            self.logger.info(f"Password reset requested for user: {mask_email(user.email)}")
            
            return create_success_response(
                message="If the email exists, a password reset link has been sent",
                data={
                    "reset_requested": True,
                    "email_sent": email_sent,
                    "message": "If an account with this email exists, you will receive a password reset link shortly."
                }
            )
            
        except ApiException:
            # Re-raise ApiException as-is
            raise
        except Exception as e:
            self.logger.error(f"Password reset request failed for email {mask_email(email)}: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Password reset request failed",
                field="email"
            )
    
    async def confirm_password_reset(self, reset_token: str, new_password: str) -> Dict[str, Any]:
        """
        Confirm password reset using reset token.
        
        Args:
            reset_token: Password reset token
            new_password: New password
            
        Returns:
            ApiResponse confirming password reset
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            # Find user by reset token
            result = await self.db.execute(
                select(User).where(User.password_reset_token == reset_token)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                self.logger.warning(f"Password reset attempt with invalid token: {reset_token[:10]}...")
                raise_error_response(
                    status_code=400,
                    message="Invalid or expired reset token",
                    field="reset_token"
                )
            
            # Check if token is expired
            if user.password_reset_token_expires and user.password_reset_token_expires < datetime.utcnow():
                self.logger.warning(f"Password reset attempt with expired token for user: {mask_email(user.email)}")
                raise_error_response(
                    status_code=400,
                    message="Reset token has expired",
                    field="reset_token"
                )
            
            # Check if user is active
            if not user.is_active:
                self.logger.warning(f"Password reset attempt for inactive user: {mask_email(user.email)}")
                raise_error_response(
                    status_code=400,
                    message="Account is deactivated",
                    field="reset_token"
                )
            
            # Update password
            user.password_hash = self.get_password_hash(new_password)
            user.password_reset_token = None  # Clear the token
            user.password_reset_token_expires = None
            user.failed_attempts = 0  # Reset failed attempts
            user.locked_until = None  # Unlock account
            user.updated_at = datetime.utcnow()
            
            # Revoke all refresh tokens for security
            revoked_count = await self.revoke_all_user_tokens(user.id)
            
            await self.db.commit()
            
            self.logger.info(f"Password reset completed successfully for user: {mask_email(user.email)}")
            
            return create_success_response(
                message="Password reset successfully",
                data={
                    "password_reset": True,
                    "tokens_revoked": revoked_count,
                    "message": "Your password has been reset successfully. Please log in with your new password."
                }
            )
            
        except ApiException:
            # Re-raise ApiException as-is
            raise
        except Exception as e:
            self.logger.error(f"Password reset confirmation failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Password reset failed",
                field="reset_token"
            )
    
    async def verify_email(self, verification_token: str) -> Dict[str, Any]:
        """
        Verify user email using verification token.
        
        Args:
            verification_token: Email verification token
            
        Returns:
            ApiResponse with verification status
            
        Raises:
            ApiException: For various error conditions
        """
        try:
            # Find user by verification token
            result = await self.db.execute(
                select(User).where(User.verification_token == verification_token)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                self.logger.warning(f"Email verification attempt with invalid token: {verification_token[:10]}...")
                raise_error_response(
                    status_code=400,
                    message="Invalid verification token",
                    field="token"
                )
            
            # Check if token is expired
            if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
                self.logger.warning(f"Email verification attempt with expired token for user: {mask_email(user.email)}")
                raise_error_response(
                    status_code=400,
                    message="Verification token has expired",
                    field="token"
                )
            
            # Check if already verified
            if user.is_verified:
                self.logger.info(f"Email verification attempt for already verified user: {mask_email(user.email)}")
                raise_error_response(
                    status_code=400,
                    message="Email is already verified",
                    field="email"
                )
            
            # Update user verification status
            user.is_verified = True
            user.verification_token = None  # Clear the token
            user.verification_token_expires = None
            
            await self.db.commit()
            
            self.logger.info(f"Email verified successfully for user: {mask_email(user.email)}")
            
            return create_success_response(
                message="Email verified successfully",
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "is_verified": user.is_verified
                    }
                }
            )
            
        except ApiException:
            # Re-raise ApiException as-is
            raise
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Email verification failed",
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

