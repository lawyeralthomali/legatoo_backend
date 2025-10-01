"""
User service for business logic operations.

This module contains business logic for user-related operations,
following the Single Responsibility Principle and Dependency Inversion.
"""

from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.user_repository import UserRepository
from ..repositories.profile_repository import ProfileRepository
from ..schemas.user_schemas import UserResponse
from ..schemas.profile_schemas import ProfileResponse
from ..utils.exceptions import NotFoundException, ValidationException
from ..config.enhanced_logging import get_logger

logger = get_logger(__name__)


class UserService:
    """
    Service class for user business logic operations.
    
    Following clean architecture: Services create and manage their own repositories.
    Routes should not know about repositories.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize user service with database session.
        
        Creates repository instances internally, following dependency inversion principle.
        
        Args:
            db: Async database session
        """
        self.user_repository = UserRepository(db)
        self.profile_repository = ProfileRepository(db)
    
    async def get_user_by_id(self, user_id: Union[UUID, int]) -> UserResponse:
        """
        Get user by ID with business validation.
        
        Args:
            user_id: User ID
            
        Returns:
            UserResponse with user data
            
        Raises:
            NotFoundException: If user not found
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise NotFoundException(
                resource="User",
                field="id"
            )
        return user
    
    async def get_user_by_email(self, email: str) -> UserResponse:
        """
        Get user by email with business validation.
        
        Args:
            email: User's email address
            
        Returns:
            UserResponse with user data
            
        Raises:
            NotFoundException: If user not found
        """
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise NotFoundException(
                resource="User",
                field="email"
            )
        return user
    
    async def get_user_profile(self, user_id: Union[UUID, int]) -> ProfileResponse:
        """
        Get user's profile with business validation.
        
        Args:
            user_id: User ID
            
        Returns:
            ProfileResponse with profile data
            
        Raises:
            NotFoundException: If profile not found
        """
        profile = await self.profile_repository.get_by_user_id(user_id)
        if not profile:
            raise NotFoundException(
                resource="Profile",
                field="user_id"
            )
        return profile
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """
        Get all users with pagination and business rules.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of UserResponse objects
            
        Raises:
            ValidationException: If pagination parameters are invalid
        """
        if skip < 0:
            raise ValidationException(
                message="Skip parameter must be non-negative",
                field="skip"
            )
        
        if limit <= 0 or limit > 1000:
            raise ValidationException(
                message="Limit must be between 1 and 1000",
                field="limit"
            )
        
        return await self.user_repository.get_all_users(skip=skip, limit=limit)
    
    async def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """
        Search users by email with business validation.
        
        Args:
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching UserResponse objects
            
        Raises:
            ValidationException: If search parameters are invalid
        """
        if not query or len(query.strip()) < 2:
            raise ValidationException(
                message="Search query must be at least 2 characters",
                field="query"
            )
        
        if skip < 0:
            raise ValidationException(
                message="Skip parameter must be non-negative",
                field="skip"
            )
        
        if limit <= 0 or limit > 1000:
            raise ValidationException(
                message="Limit must be between 1 and 1000",
                field="limit"
            )
        
        # For this implementation, we'll search by email
        # In a real system, you might have a more sophisticated search
        users = await self.user_repository.get_all_users(skip=skip, limit=limit)
        query_lower = query.lower()
        
        return [
            user for user in users
            if query_lower in user.email.lower()
        ]
    
    async def get_user_with_profile(self, user_id: Union[UUID, int]) -> Dict[str, Any]:
        """
        Get user with their profile in a single response.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing both user and profile data
            
        Raises:
            NotFoundException: If user or profile not found
        """
        user = await self.get_user_by_id(user_id)
        profile = await self.get_user_profile(user_id)
        
        return {
            "user": user.dict(),
            "profile": profile.dict()
        }
    
    async def validate_user_exists(self, user_id: Union[UUID, int]) -> bool:
        """
        Validate that a user exists without returning full data.
        
        Args:
            user_id: User ID to validate
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            await self.get_user_by_id(user_id)
            return True
        except NotFoundException:
            return False
    
    @staticmethod
    def get_user_auth_data(token_data: 'TokenData') -> 'UserAuth':
        """
        Convert TokenData to UserAuth format.
        
        Args:
            token_data: JWT token data
            
        Returns:
            UserAuth object with user authentication data
        """
        from ..schemas.profile_schemas import ProfileResponse
        
        return UserAuth(
            user_id=token_data.user_id,
            email=token_data.email,
            aud=token_data.aud,
            role=token_data.role,
            profile=None  # Profile will be loaded separately if needed
        )