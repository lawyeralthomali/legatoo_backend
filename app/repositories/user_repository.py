"""
User repository implementation.

This module provides concrete implementation of user data access operations,
following the Repository pattern for clean separation of concerns.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta

from .base import IUserRepository, BaseRepository
from ..models.user import User
from ..schemas.user_schemas import UserCreate, UserResponse


class UserRepository(IUserRepository, BaseRepository):
    """Concrete implementation of user repository."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize user repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, User)
    
    async def get_by_email(self, email: str) -> Optional[UserResponse]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            UserResponse if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        return UserResponse.model_validate(user) if user else None
    
    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email exists, False otherwise
        """
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created UserResponse
            
        Raises:
            IntegrityError: If user with email already exists
        """
        try:
            user_dict = user_data.dict()
            user = User(**user_dict)
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            return UserResponse.model_validate(user)
            
        except IntegrityError as e:
            await self.db.rollback()
            if "email" in str(e.orig).lower():
                raise IntegrityError(
                    statement=e.statement,
                    params=e.params,
                    orig=e.orig
                )
            raise e
    
    async def get_by_id(self, user_id: int) -> Optional[UserResponse]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserResponse if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        return UserResponse.model_validate(user) if user else None
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """
        Get all users with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of UserResponse objects
        """
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        users = result.scalars().all()
        return [UserResponse.model_validate(user) for user in users]
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[UserResponse]:
        """
        Update user by ID.
        
        Args:
            user_id: User ID
            user_data: User update data
            
        Returns:
            Updated UserResponse if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            for key, value in user_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            await self.db.commit()
            await self.db.refresh(user)
            
            return UserResponse.model_validate(user)
            
        except IntegrityError as e:
            await self.db.rollback()
            raise e
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Delete user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        await self.db.delete(user)
        await self.db.commit()
        return True
    
    # ==================== Auth-specific methods ====================
    
    async def get_user_model_by_email(self, email: str) -> Optional[User]:
        """
        Get user model (not UserResponse) by email for auth operations.
        
        Args:
            email: User's email address
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_model_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user model (not UserResponse) by ID for auth operations.
        
        Args:
            user_id: User ID
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_verification_token(self, token: str) -> Optional[User]:
        """
        Get user by verification token.
        
        Args:
            token: Verification token
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.verification_token == token)
        )
        return result.scalar_one_or_none()
    
    async def get_by_password_reset_token(self, token: str) -> Optional[User]:
        """
        Get user by password reset token.
        
        Args:
            token: Password reset token
            
        Returns:
            User model if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.password_reset_token == token)
        )
        return result.scalar_one_or_none()
    
    async def create_user_with_verification(
        self,
        email: str,
        password_hash: str,
        verification_token: str,
        verification_expires: datetime,
        role: str
    ) -> User:
        """
        Create a new user with verification token.
        
        Args:
            email: User's email
            password_hash: Hashed password
            verification_token: Email verification token
            verification_expires: Token expiration datetime
            role: User role
            
        Returns:
            Created User model
        """
        user = User(
            email=email,
            password_hash=password_hash,
            is_active=True,
            is_verified=False,
            verification_token=verification_token,
            verification_token_expires=verification_expires,
            failed_attempts=0,
            email_sent=False,
            role=role
        )
        
        self.db.add(user)
        await self.db.flush()  # Get the user ID without committing
        
        return user
    
    async def increment_failed_attempts(self, user_id: int, max_attempts: int = 5, lockout_minutes: int = 30) -> None:
        """
        Increment failed login attempts and lock account if needed.
        
        Args:
            user_id: User ID
            max_attempts: Maximum allowed failed attempts
            lockout_minutes: Minutes to lock account
        """
        user = await self.get_user_model_by_id(user_id)
        if user:
            user.failed_attempts += 1
            
            # Lock account if max attempts reached
            if user.failed_attempts >= max_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
            
            await self.db.commit()
    
    async def reset_failed_attempts(self, user_id: int) -> None:
        """
        Reset failed login attempts and update last login.
        
        Args:
            user_id: User ID
        """
        user = await self.get_user_model_by_id(user_id)
        if user:
            user.failed_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            await self.db.commit()
    
    async def mark_email_sent(self, user_id: int) -> None:
        """
        Mark verification email as sent.
        
        Args:
            user_id: User ID
        """
        user = await self.get_user_model_by_id(user_id)
        if user:
            user.email_sent = True
            user.email_sent_at = datetime.utcnow()
            await self.db.commit()
    
    async def verify_user_email(self, user_id: int) -> None:
        """
        Mark user email as verified.
        
        Args:
            user_id: User ID
        """
        user = await self.get_user_model_by_id(user_id)
        if user:
            user.is_verified = True
            user.verification_token = None
            user.verification_token_expires = None
            await self.db.commit()
    
    async def set_password_reset_token(
        self,
        user_id: int,
        reset_token: str,
        reset_expires: datetime
    ) -> None:
        """
        Set password reset token for user.
        
        Args:
            user_id: User ID
            reset_token: Password reset token
            reset_expires: Token expiration datetime
        """
        user = await self.get_user_model_by_id(user_id)
        if user:
            user.password_reset_token = reset_token
            user.password_reset_token_expires = reset_expires
            await self.db.commit()
    
    async def update_password(self, user_id: int, new_password_hash: str) -> None:
        """
        Update user password and clear reset token.
        
        Args:
            user_id: User ID
            new_password_hash: New hashed password
        """
        user = await self.get_user_model_by_id(user_id)
        if user:
            user.password_hash = new_password_hash
            user.password_reset_token = None
            user.password_reset_token_expires = None
            user.failed_attempts = 0
            user.locked_until = None
            user.updated_at = datetime.utcnow()
            await self.db.commit()
