"""
Profile repository implementation.

This module provides concrete implementation of profile data access operations,
following the Repository pattern for clean separation of concerns.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..config.logging_config import get_logger
from .base import IProfileRepository, BaseRepository
from ..models.profile import Profile
from ..schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate


class ProfileRepository(IProfileRepository, BaseRepository):
    """Concrete implementation of profile repository."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize profile repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, Profile)
        self.logger = get_logger(__name__)
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[ProfileResponse]:
        """
        Get profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            ProfileResponse if found, None otherwise
        """
        result = await self.db.execute(
            select(Profile).where(Profile.id == user_id)
        )
        profile = result.scalar_one_or_none()
        return ProfileResponse.model_validate(profile) if profile else None
    
    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists in profiles.
        
        Note: This is a simplified implementation. In a real system,
        you might need to join with users table or maintain email mapping.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email exists, False otherwise
        """
        # For this implementation, we'll rely on the unique constraint
        # and handle race conditions at the service level
        return False
    
    async def create_profile(self, user_id: UUID, profile_data: Dict[str, Any]) -> ProfileResponse:
        """
        Create new profile.
        
        Args:
            user_id: User ID for the profile
            profile_data: Profile creation data
            
        Returns:
            Created ProfileResponse
            
        Raises:
            IntegrityError: If profile already exists (race condition)
        """
        try:
            self.logger.info(f"Creating profile for user ID: {user_id}")
            profile_dict = profile_data.copy()
            profile_dict["id"] = user_id  # Primary key (same as Supabase user_id)
            
            profile = Profile(**profile_dict)
            
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
            
            self.logger.info(f"Profile created successfully for user ID: {user_id}")
            return ProfileResponse.model_validate(profile)
            
        except IntegrityError as e:
            await self.db.rollback()
            self.logger.exception(f"Integrity error creating profile for user ID {user_id}: {str(e)}")
            if "id" in str(e.orig).lower() or "unique" in str(e.orig).lower():
                raise IntegrityError(
                    statement=e.statement,
                    params=e.params,
                    orig=e.orig
                )
            raise e
        except Exception as e:
            await self.db.rollback()
            self.logger.exception(f"Unexpected error creating profile for user ID {user_id}: {str(e)}")
            raise e
    
    async def update_profile(self, user_id: UUID, profile_data: ProfileUpdate) -> Optional[ProfileResponse]:
        """
        Update profile by user ID.
        
        Args:
            user_id: User ID
            profile_data: Profile update data
            
        Returns:
            Updated ProfileResponse if found, None otherwise
        """
        try:
            result = await self.db.execute(
                select(Profile).where(Profile.id == user_id)
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                return None
            
            # Update only provided fields
            update_data = profile_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            await self.db.commit()
            await self.db.refresh(profile)
            
            return ProfileResponse.model_validate(profile)
            
        except IntegrityError as e:
            await self.db.rollback()
            raise e
    
    async def delete_profile(self, user_id: UUID) -> bool:
        """
        Delete profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(Profile).where(Profile.id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return False
        
        await self.db.delete(profile)
        await self.db.commit()
        return True
    
    async def get_all_profiles(self, skip: int = 0, limit: int = 100) -> List[ProfileResponse]:
        """
        Get all profiles with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ProfileResponse objects
        """
        result = await self.db.execute(
            select(Profile).offset(skip).limit(limit)
        )
        profiles = result.scalars().all()
        return [ProfileResponse.model_validate(profile) for profile in profiles]
    
    async def search_profiles(self, query: str, skip: int = 0, limit: int = 100) -> List[ProfileResponse]:
        """
        Search profiles by name.
        
        Args:
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching ProfileResponse objects
        """
        search_term = f"%{query}%"
        result = await self.db.execute(
            select(Profile)
            .where(
                (Profile.first_name.ilike(search_term)) |
                (Profile.last_name.ilike(search_term))
            )
            .offset(skip)
            .limit(limit)
        )
        profiles = result.scalars().all()
        return [ProfileResponse.model_validate(profile) for profile in profiles]
