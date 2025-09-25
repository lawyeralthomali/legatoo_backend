

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import logging

from ..models.profile import Profile
from ..schemas.profile import ProfileCreate

logger = logging.getLogger(__name__)


class IProfileRepository(ABC):

    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:

        pass
    
    @abstractmethod
    async def get_profile_by_id(self, user_id: UUID) -> Optional[Profile]:
        """
        Get profile by user ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            Profile instance if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create_profile(self, user_id: UUID, profile_data: ProfileCreate) -> Profile:
        """
        Create a new profile.
        
        Args:
            user_id: User ID for the profile
            profile_data: Profile creation data
            
        Returns:
            Created Profile instance
            
        Raises:
            IntegrityError: If profile already exists (race condition)
        """
        pass


class ProfileRepository(IProfileRepository):
    """Concrete implementation of profile repository using AsyncSession."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize profile repository.
        
        Args:
            db: AsyncSession for database operations
        """
        self.db = db
    
    async def email_exists(self, email: str) -> bool:
  
        # Note: This is a simplified check. In a real implementation,
        # you might need to join with auth.users or maintain email mapping
        # For now, we'll rely on the unique constraint and handle race conditions
        return False  # Simplified for this implementation
    
    async def get_profile_by_id(self, user_id: UUID) -> Optional[Profile]:

        result = await self.db.execute(
            select(Profile).where(Profile.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_profile(self, user_id: UUID, profile_data: ProfileCreate) -> Profile:
    
        try:
            profile = Profile(
                id=user_id,
                first_name=profile_data.first_name,
                last_name=profile_data.last_name,
                phone_number=profile_data.phone_number,
                avatar_url=profile_data.avatar_url,
                account_type=profile_data.account_type.value,
            )
            
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
            
            return profile
            
        except IntegrityError as e:
            # Handle race condition - profile already exists
            await self.db.rollback()
            logger.warning(f"Profile creation failed due to race condition: {str(e)}")
            raise e
        except Exception as e:
            # Handle other database errors
            await self.db.rollback()
            logger.error(f"Profile creation failed: {str(e)}")
            raise e
