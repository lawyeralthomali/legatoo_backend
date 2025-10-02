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
    """
    Service class for profile business logic operations.
    
    Following clean architecture: Services create and manage their own repositories.
    """
    
    def __init__(self, db):
        """
        Initialize profile service with database session.
        
        Creates repository internally, following dependency inversion principle.
        
        Args:
            db: Async database session
        """
        from ..repositories.profile_repository import ProfileRepository
        self.profile_repository = ProfileRepository(db)
    
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
    
    async def get_profile_by_id(self, user_id: Union[UUID, int]) -> Optional[ProfileResponse]:
        """
        Get profile by user ID.
        
        Args:
            user_id: User ID to search for (UUID or int)
            
        Returns:
            ProfileResponse if found, None otherwise
        """
        # Convert UUID to int if needed (assuming UUID can be converted to int)
        if isinstance(user_id, UUID):
            # Convert UUID to int for database operations
            user_id_int = int(str(user_id).replace('-', ''), 16)
        else:
            user_id_int = user_id
            
        profile = await self.profile_repository.get_by_user_id(user_id_int)
        return profile
    
    async def get_profile_response_by_id(self, user_id: Union[UUID, int]) -> Optional[ProfileResponse]:
        """
        Get profile response by user ID.
        
        Args:
            user_id: User ID to search for (UUID or int)
            
        Returns:
            ProfileResponse if found, None otherwise
        """
        return await self.get_profile_by_id(user_id)
    
    async def create_profile_if_not_exists(self, user_id: Union[UUID, int]) -> ProfileResponse:
        """
        Create a default profile if it doesn't exist for the user.
        
        This method is used when retrieving a profile and none exists.
        It creates a minimal profile with default values.
        
        Args:
            user_id: User ID (UUID or int)
            
        Returns:
            ProfileResponse with created profile data
        """
        try:
            logger.info(f"Creating default profile for user ID: {user_id}")
            
            # Convert UUID to int if needed
            if isinstance(user_id, UUID):
                user_id_int = int(str(user_id).replace('-', ''), 16)
            else:
                user_id_int = user_id
            
            # Create a minimal profile with default values
            profile_data = ProfileCreate(
                email=f"user_{user_id_int}@example.com",  # Default email
                first_name="User",
                last_name="User",
                phone_number=None,
                avatar_url=None,
                account_type=AccountType.PERSONAL
            )
            
            # Create the profile
            created_profile = await self.profile_repository.create_profile(user_id_int, profile_data)
            return created_profile
                
        except Exception as e:
            logger.error(f"Error creating default profile for user {user_id}: {str(e)}")
            raise

    async def create_or_update_profile(
        self, 
        user_id: Union[UUID, int], 
        profile_data: ProfileUpdate
    ) -> ProfileResponse:
        """
        Create or update profile for a user.
        
        If profile exists, update it. If not, create a new one.
        
        Args:
            user_id: User ID (UUID or int)
            profile_data: Profile update data
            
        Returns:
            ProfileResponse with created/updated profile data
        """
        try:
            # Convert UUID to int if needed
            if isinstance(user_id, UUID):
                user_id_int = int(str(user_id).replace('-', ''), 16)
            else:
                user_id_int = user_id
            
            # First, try to get existing profile
            existing_profile = await self.profile_repository.get_by_user_id(user_id_int)
            
            if existing_profile:
                # Profile exists, update it
                logger.info(f"Updating existing profile for user ID: {user_id_int}")
                updated_profile = await self.profile_repository.update_profile(user_id_int, profile_data)
                if updated_profile:
                    return updated_profile
                else:
                    # This shouldn't happen since we just found the profile
                    raise Exception("Failed to update existing profile")
            else:
                # Profile doesn't exist, create it
                logger.info(f"Creating new profile for user ID: {user_id_int}")
                
                # Convert ProfileUpdate to ProfileCreate for creation
                profile_dict = profile_data.model_dump(exclude_unset=True)
                
                # Set required fields with defaults if not provided
                profile_dict["email"] = profile_dict.get("email", f"user_{user_id_int}@example.com")
                profile_dict["first_name"] = profile_dict.get("first_name", "User")
                profile_dict["last_name"] = profile_dict.get("last_name", "User")
                
                # Create ProfileCreate object
                create_data = ProfileCreate(**profile_dict)
                
                # Create the profile
                created_profile = await self.profile_repository.create_profile(user_id_int, create_data)
                return created_profile
                
        except Exception as e:
            logger.error(f"Error in create_or_update_profile for user {user_id}: {str(e)}")
            raise