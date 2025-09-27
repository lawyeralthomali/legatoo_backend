"""
User repository implementation.

This module provides concrete implementation of user data access operations,
following the Repository pattern for clean separation of concerns.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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
