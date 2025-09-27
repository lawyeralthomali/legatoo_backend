"""
Profile repository implementation.

This module provides a self-contained, production-ready implementation of profile data access operations
with comprehensive error handling, validation, and logging.
"""

from typing import Optional, List, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from ..config.logging_config import get_logger
from ..models.profile import Profile
from ..schemas.profile_schemas import ProfileCreate, ProfileResponse, ProfileUpdate


class ProfileRepository:
    """
    Self-contained profile repository for database operations.
    
    This repository handles all profile-related database operations with comprehensive
    error handling, validation, and logging. It ensures data integrity and provides
    clear feedback for all operations.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize profile repository.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.logger = get_logger(__name__)
    
    async def get_by_user_id(self, user_id: int) -> Optional[ProfileResponse]:
        """
        Get profile by user ID.
        
        Args:
            user_id: User ID (int)
            
        Returns:
            ProfileResponse if found, None otherwise
            
        Raises:
            Exception: If database operation fails
        """
        try:
            self.logger.info(f"Fetching profile for user ID: {user_id}")
            
            result = await self.db.execute(
                select(Profile).where(Profile.id == user_id)
            )
            profile = result.scalar_one_or_none()
            
            if profile:
                self.logger.info(f"Profile found for user ID: {user_id}")
                return ProfileResponse.model_validate(profile)
            else:
                self.logger.info(f"No profile found for user ID: {user_id}")
                return None
                
        except Exception as e:
            self.logger.exception(f"Error fetching profile for user ID {user_id}: {str(e)}")
            raise e
    
    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists in profiles.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email exists, False otherwise
            
        Raises:
            Exception: If database operation fails
        """
        try:
            self.logger.info(f"Checking if email exists: {email}")
            
            result = await self.db.execute(
                select(Profile).where(Profile.email == email)
            )
            profile = result.scalar_one_or_none()
            
            exists = profile is not None
            self.logger.info(f"Email {email} exists: {exists}")
            return exists
            
        except Exception as e:
            self.logger.exception(f"Error checking email existence for {email}: {str(e)}")
            raise e
    
    async def create_profile(
        self, 
        user_id: int, 
        profile_data: Union[Dict[str, Any], ProfileCreate]
    ) -> ProfileResponse:
        """
        Create new profile with comprehensive validation and error handling.
        
        Args:
            user_id: User ID for the profile (int)
            profile_data: Profile creation data (dict or ProfileCreate)
            
        Returns:
            Created ProfileResponse
            
        Raises:
            IntegrityError: If profile already exists or email is duplicate
            ValueError: If required fields are missing
            Exception: For other database errors
        """
        try:
            self.logger.info(f"Creating profile for user ID: {user_id}")
            
            # Convert ProfileCreate to dict if needed
            if isinstance(profile_data, ProfileCreate):
                profile_dict = profile_data.model_dump()
            else:
                profile_dict = profile_data.copy()
            
            # Extract email for validation
            email = profile_dict.get("email")
            if not email:
                raise ValueError("Email is required for profile creation")
            
            # Check if email already exists
            if await self.email_exists(email):
                self.logger.warning(f"Email already exists: {email}")
                raise IntegrityError(
                    statement="INSERT INTO profiles",
                    params={"email": email},
                    orig=Exception(f"Email {email} already exists")
                )
            
            # Check if user_id already exists
            existing_profile = await self.get_by_user_id(user_id)
            if existing_profile:
                self.logger.warning(f"Profile already exists for user ID: {user_id}")
                raise IntegrityError(
                    statement="INSERT INTO profiles",
                    params={"id": user_id},
                    orig=Exception(f"Profile for user {user_id} already exists")
                )
            
            # Prepare profile data with all required fields
            profile_dict["id"] = user_id  # Primary key (same as Supabase user_id)
            
            # Ensure all required fields are present
            required_fields = ["first_name", "last_name", "email"]
            for field in required_fields:
                if field not in profile_dict or not profile_dict[field]:
                    raise ValueError(f"Required field '{field}' is missing or empty")
            
            # Create profile instance
            profile = Profile(**profile_dict)
            
            # Add to session and commit
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
            
            self.logger.info(f"Profile created successfully for user ID: {user_id}, email: {email}")
            return ProfileResponse.model_validate(profile)
            
        except IntegrityError as e:
            await self.db.rollback()
            self.logger.exception(f"Integrity error creating profile for user ID {user_id}: {str(e)}")
            raise e
        except ValueError as e:
            await self.db.rollback()
            self.logger.error(f"Validation error creating profile for user ID {user_id}: {str(e)}")
            raise e
        except Exception as e:
            await self.db.rollback()
            self.logger.exception(f"Unexpected error creating profile for user ID {user_id}: {str(e)}")
            raise e
    
    async def update_profile(
        self, 
        user_id: int, 
        profile_data: Union[ProfileUpdate, Dict[str, Any]]
    ) -> Optional[ProfileResponse]:
        """
        Update profile by user ID with comprehensive validation.
        
        Args:
            user_id: User ID (int)
            profile_data: Profile update data (ProfileUpdate or dict)
            
        Returns:
            Updated ProfileResponse if found, None otherwise
            
        Raises:
            IntegrityError: If email is duplicate
            ValueError: If validation fails
            Exception: For other database errors
        """
        try:
            self.logger.info(f"Updating profile for user ID: {user_id}")
            
            # Convert ProfileUpdate to dict if needed
            if isinstance(profile_data, ProfileUpdate):
                update_data = profile_data.model_dump(exclude_unset=True)
            else:
                update_data = profile_data.copy()
            
            # Check if profile exists
            result = await self.db.execute(
                select(Profile).where(Profile.id == user_id)
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                self.logger.warning(f"Profile not found for user ID: {user_id}")
                return None
            
            # Check email uniqueness if email is being updated
            if "email" in update_data and update_data["email"] != profile.email:
                if await self.email_exists(update_data["email"]):
                    self.logger.warning(f"Email already exists: {update_data['email']}")
                    raise IntegrityError(
                        statement="UPDATE profiles",
                        params={"email": update_data["email"]},
                        orig=Exception(f"Email {update_data['email']} already exists")
                    )
            
            # Update only provided fields
            for key, value in update_data.items():
                if hasattr(profile, key) and value is not None:
                    setattr(profile, key, value)
            
            # Update timestamp (handled automatically by SQLAlchemy)
            
            await self.db.commit()
            await self.db.refresh(profile)
            
            self.logger.info(f"Profile updated successfully for user ID: {user_id}")
            return ProfileResponse.model_validate(profile)
            
        except IntegrityError as e:
            await self.db.rollback()
            self.logger.exception(f"Integrity error updating profile for user ID {user_id}: {str(e)}")
            raise e
        except ValueError as e:
            await self.db.rollback()
            self.logger.error(f"Validation error updating profile for user ID {user_id}: {str(e)}")
            raise e
        except Exception as e:
            await self.db.rollback()
            self.logger.exception(f"Unexpected error updating profile for user ID {user_id}: {str(e)}")
            raise e
    
    async def delete_profile(self, user_id: int) -> bool:
        """
        Delete profile by user ID with proper error handling.
        
        Args:
            user_id: User ID (int)
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            Exception: If database operation fails
        """
        try:
            self.logger.info(f"Deleting profile for user ID: {user_id}")
            
            result = await self.db.execute(
                select(Profile).where(Profile.id == user_id)
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                self.logger.warning(f"Profile not found for deletion, user ID: {user_id}")
                return False
            
            await self.db.delete(profile)
            await self.db.commit()
            
            self.logger.info(f"Profile deleted successfully for user ID: {user_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            self.logger.exception(f"Error deleting profile for user ID {user_id}: {str(e)}")
            raise e
    
    async def get_all_profiles(self, skip: int = 0, limit: int = 100) -> List[ProfileResponse]:
        """
        Get all profiles with pagination and proper error handling.
        
        Args:
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100, max: 1000)
            
        Returns:
            List of ProfileResponse objects
            
        Raises:
            Exception: If database operation fails
        """
        try:
            # Validate pagination parameters
            skip = max(0, skip)
            limit = min(max(1, limit), 1000)  # Cap at 1000 for performance
            
            self.logger.info(f"Fetching profiles with pagination - skip: {skip}, limit: {limit}")
            
            result = await self.db.execute(
                select(Profile)
                .order_by(Profile.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            profiles = result.scalars().all()
            
            self.logger.info(f"Found {len(profiles)} profiles")
            return [ProfileResponse.model_validate(profile) for profile in profiles]
            
        except Exception as e:
            self.logger.exception(f"Error fetching profiles with pagination - skip: {skip}, limit: {limit}: {str(e)}")
            raise e
    
    async def search_profiles(self, query: str, skip: int = 0, limit: int = 100) -> List[ProfileResponse]:
        """
        Search profiles by name with case-insensitive matching and proper error handling.
        
        Args:
            query: Search query string
            skip: Number of records to skip (default: 0)
            limit: Maximum number of records to return (default: 100, max: 1000)
            
        Returns:
            List of matching ProfileResponse objects
            
        Raises:
            ValueError: If query is empty or too short
            Exception: If database operation fails
        """
        try:
            # Validate search query
            if not query or len(query.strip()) < 2:
                raise ValueError("Search query must be at least 2 characters long")
            
            # Validate pagination parameters
            skip = max(0, skip)
            limit = min(max(1, limit), 1000)  # Cap at 1000 for performance
            
            search_term = f"%{query.strip()}%"
            
            self.logger.info(f"Searching profiles with query: '{query}', skip: {skip}, limit: {limit}")
            
            result = await self.db.execute(
                select(Profile)
                .where(
                    (Profile.first_name.ilike(search_term)) |
                    (Profile.last_name.ilike(search_term)) |
                    (Profile.email.ilike(search_term))
                )
                .order_by(Profile.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            profiles = result.scalars().all()
            
            self.logger.info(f"Found {len(profiles)} profiles matching query: '{query}'")
            return [ProfileResponse.model_validate(profile) for profile in profiles]
            
        except ValueError as e:
            self.logger.warning(f"Invalid search query: {str(e)}")
            raise e
        except Exception as e:
            self.logger.exception(f"Error searching profiles with query '{query}': {str(e)}")
            raise e