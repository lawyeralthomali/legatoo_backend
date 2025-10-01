"""
Profile service for business logic operations.

This module contains business rules and orchestration for profile operations,
following the Single Responsibility Principle.
"""

from typing import Optional, Union
from uuid import UUID
from sqlalchemy.exc import IntegrityError

from ..repositories.profile_repository import ProfileRepository
from ..models.profile import AccountType
from ..schemas.profile_schemas import ProfileResponse, ProfileCreate, ProfileUpdate
from ..config.enhanced_logging import get_logger

logger = get_logger(__name__)


class ProfileService:
    """Service class for profile business logic operations."""
    
    def __init__(self, profile_repository: ProfileRepository):
        """
        Initialize profile service.
        
        Args:
            profile_repository: Repository for profile data access
        """
        self.profile_repository = profile_repository
    
    async def check_email_uniqueness(self, email: str) -> bool:
        """
        Check if email is unique (not already registered).
        
        This method implements the business rule for email uniqueness.
        In a real implementation, this might involve checking both
        Supabase auth.users and local profiles table.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email is unique, False if already exists
        """
        # For this implementation, we'll rely on the repository's email check
        # In a production system, you might want to check Supabase auth.users
        # or maintain a separate email mapping table
        return not await self.profile_repository.email_exists(email)
    
    async def create_profile_for_user(
        self, 
        user_id: Union[UUID, int], 
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> ProfileResponse:
        """
        Create a profile for a user with business rules applied.
        
        Applies business rules such as default values and validation.
        
        Args:
            user_id: User ID from Supabase
            email: User's email address
            first_name: User's first name
            last_name: User's last name
            phone_number: User's phone number
            avatar_url: User's avatar URL
            
        Returns:
            ProfileResponse with created profile data
            
        Raises:
            IntegrityError: If profile already exists (race condition)
        """
        # Apply business rules for default values
        profile_data = ProfileCreate(
            email=email,
            first_name=first_name or "User",
            last_name=last_name or "User",
            phone_number=phone_number,
            avatar_url=avatar_url,
            account_type=AccountType.PERSONAL  # Default account type
        )
        
        try:
            # Create profile using repository
            profile = await self.profile_repository.create_profile(user_id, profile_data)
            
            # Convert to response format
            return ProfileResponse.from_orm(profile)
            
        except IntegrityError:
            # Re-raise integrity errors for upstream handling
            raise
        except Exception as e:
            # Log and re-raise other errors
            logger.error(f"Profile service error: {str(e)}")
            raise
    
    async def get_profile_by_id(self, user_id: UUID) -> Optional[ProfileResponse]:
        """
        Get profile by user ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            ProfileResponse if found, None otherwise
        """
        profile = await self.profile_repository.get_by_user_id(user_id)
        return profile
    
    async def get_profile_response_by_id(self, user_id: UUID) -> Optional[ProfileResponse]:
        """
        Get profile response by user ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            ProfileResponse if found, None otherwise
        """
        return await self.get_profile_by_id(user_id)
    
    async def create_profile_if_not_exists(self, user_id: UUID) -> ProfileResponse:
        """
        Create a default profile if it doesn't exist.
        
        Args:
            user_id: User ID to create profile for
            
        Returns:
            Created ProfileResponse
        """
        return await self.create_profile_for_user(
            user_id=user_id,
            email="default@example.com",  # Default email for auto-created profiles
            first_name="User",
            last_name="User"
        )