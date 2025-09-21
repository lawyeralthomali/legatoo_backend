from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional
from uuid import UUID

from ..models.profile import Profile
from ..schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_profile(self, user_id: UUID, profile_data: ProfileCreate) -> ProfileResponse:
        """
        Create a new profile for a user.
        
        Args:
            user_id: The user's UUID from Supabase auth.users
            profile_data: Profile data to create
            
        Returns:
            ProfileResponse: Created profile data
            
        Raises:
            HTTPException: If profile already exists or creation fails
        """
        try:
            # Check if profile already exists
            existing_profile = await self.get_profile_by_id(user_id)
            if existing_profile:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Profile already exists for this user"
                )
            
            # Create new profile
            profile = Profile(
                id=user_id,
                full_name=profile_data.full_name,
                avatar_url=profile_data.avatar_url,
                bio=profile_data.bio
            )
            
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
            
            return ProfileResponse.from_orm(profile)
            
        except IntegrityError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Profile already exists for this user"
            )

    async def get_profile_by_id(self, user_id: UUID) -> Optional[Profile]:
        """
        Get a profile by user ID.
        
        Args:
            user_id: The user's UUID
            
        Returns:
            Profile or None if not found
        """
        result = await self.db.execute(
            select(Profile).where(Profile.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_profile_response_by_id(self, user_id: UUID) -> Optional[ProfileResponse]:
        """
        Get a profile response by user ID.
        
        Args:
            user_id: The user's UUID
            
        Returns:
            ProfileResponse or None if not found
        """
        profile = await self.get_profile_by_id(user_id)
        if profile:
            return ProfileResponse.from_orm(profile)
        return None

    async def update_profile(self, user_id: UUID, profile_update: ProfileUpdate) -> Optional[ProfileResponse]:
        """
        Update a user's profile.
        
        Args:
            user_id: The user's UUID
            profile_update: Profile data to update
            
        Returns:
            ProfileResponse: Updated profile data or None if not found
            
        Raises:
            HTTPException: If update fails
        """
        try:
            # Check if profile exists
            existing_profile = await self.get_profile_by_id(user_id)
            if not existing_profile:
                return None
            
            # Prepare update data (only non-None values)
            update_data = {}
            if profile_update.full_name is not None:
                update_data["full_name"] = profile_update.full_name
            if profile_update.avatar_url is not None:
                update_data["avatar_url"] = profile_update.avatar_url
            if profile_update.bio is not None:
                update_data["bio"] = profile_update.bio
            
            if not update_data:
                return ProfileResponse.from_orm(existing_profile)
            
            # Update the profile
            await self.db.execute(
                update(Profile)
                .where(Profile.id == user_id)
                .values(**update_data)
            )
            await self.db.commit()
            
            # Return updated profile
            updated_profile = await self.get_profile_by_id(user_id)
            return ProfileResponse.from_orm(updated_profile)
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update profile: {str(e)}"
            )

    async def delete_profile(self, user_id: UUID) -> bool:
        """
        Delete a user's profile.
        
        Args:
            user_id: The user's UUID
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            # Check if profile exists
            existing_profile = await self.get_profile_by_id(user_id)
            if not existing_profile:
                return False
            
            # Delete the profile
            await self.db.execute(
                delete(Profile).where(Profile.id == user_id)
            )
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete profile: {str(e)}"
            )

    async def create_profile_if_not_exists(self, user_id: UUID, default_full_name: str = "User") -> ProfileResponse:
        """
        Create a profile if it doesn't exist, or return existing one.
        This is useful for automatic profile creation when a user signs up.
        
        Args:
            user_id: The user's UUID
            default_full_name: Default name if profile needs to be created
            
        Returns:
            ProfileResponse: Profile data
        """
        # Try to get existing profile
        existing_profile = await self.get_profile_response_by_id(user_id)
        if existing_profile:
            return existing_profile
        
        # Create new profile with default data
        profile_data = ProfileCreate(
            full_name=default_full_name,
            avatar_url=None,
            bio=None
        )
        
        return await self.create_profile(user_id, profile_data)
