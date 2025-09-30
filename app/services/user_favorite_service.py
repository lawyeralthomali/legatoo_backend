from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..repositories.user_favorite_repository import UserFavoriteRepository
from ..repositories.contract_template_repository import ContractTemplateRepository
from ..models.favorite import UserFavorite
from ..utils.api_exceptions import ApiException


class UserFavoriteService:
    """Service for user favorite business logic following SOLID principles."""
    
    def __init__(self):
        self.repository = UserFavoriteRepository()
        self.template_repository = ContractTemplateRepository()
    
    async def get_user_favorites(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> List[UserFavorite]:
        """Get all favorites for a user."""
        return await self.repository.get_user_favorites(db, user_id)
    
    async def add_favorite(
        self, 
        db: AsyncSession, 
        user_id: int, 
        template_id: int
    ) -> UserFavorite:
        """Add a template to user favorites."""
        # Validate template exists and is active
        template = await self.template_repository.get_by_id(db, template_id)
        if not template or not template.is_active:
            raise ApiException(
                status_code=400,
                message="Invalid template",
                errors=[{"field": "template_id", "message": "Template not found or inactive"}]
            )
        
        # Check if already favorited
        if await self.repository.is_favorite(db, user_id, template_id):
            raise ApiException(
                status_code=400,
                message="Already favorited",
                errors=[{"field": "template_id", "message": "Template is already in favorites"}]
            )
        
        # Add to favorites
        favorite = await self.repository.add_favorite(db, user_id, template_id)
        if not favorite:
            raise ApiException(
                status_code=500,
                message="Failed to add favorite",
                errors=[{"field": "template_id", "message": "Could not add template to favorites"}]
            )
        
        return favorite
    
    async def remove_favorite(
        self, 
        db: AsyncSession, 
        user_id: int, 
        template_id: int
    ) -> bool:
        """Remove a template from user favorites."""
        # Validate template exists
        template = await self.template_repository.get_by_id(db, template_id)
        if not template:
            raise ApiException(
                status_code=400,
                message="Invalid template",
                errors=[{"field": "template_id", "message": "Template not found"}]
            )
        
        # Check if favorited
        if not await self.repository.is_favorite(db, user_id, template_id):
            raise ApiException(
                status_code=400,
                message="Not in favorites",
                errors=[{"field": "template_id", "message": "Template is not in favorites"}]
            )
        
        # Remove from favorites
        return await self.repository.remove_favorite(db, user_id, template_id)
    
    async def toggle_favorite(
        self, 
        db: AsyncSession, 
        user_id: int, 
        template_id: int
    ) -> dict:
        """Toggle favorite status for a template."""
        # Validate template exists and is active
        template = await self.template_repository.get_by_id(db, template_id)
        if not template or not template.is_active:
            raise ApiException(
                status_code=400,
                message="Invalid template",
                errors=[{"field": "template_id", "message": "Template not found or inactive"}]
            )
        
        is_favorite = await self.repository.is_favorite(db, user_id, template_id)
        
        if is_favorite:
            await self.repository.remove_favorite(db, user_id, template_id)
            action = "removed"
        else:
            await self.repository.add_favorite(db, user_id, template_id)
            action = "added"
        
        return {
            "template_id": template_id,
            "is_favorite": not is_favorite,
            "action": action
        }
    
    async def is_favorite(
        self, 
        db: AsyncSession, 
        user_id: int, 
        template_id: int
    ) -> bool:
        """Check if a template is favorited by a user."""
        return await self.repository.is_favorite(db, user_id, template_id)
    
    async def get_favorite_by_id(
        self, 
        db: AsyncSession, 
        favorite_id: int,
        user_id: int
    ) -> UserFavorite:
        """Get a specific favorite with ownership validation."""
        favorite = await self.repository.get_by_id(db, favorite_id)
        if not favorite:
            raise ApiException(
                status_code=404,
                message="Favorite not found",
                errors=[{"field": "favorite_id", "message": "Favorite does not exist"}]
            )
        
        if favorite.user_id != user_id:
            raise ApiException(
                status_code=403,
                message="Access denied",
                errors=[{"field": "favorite_id", "message": "You don't have permission to access this favorite"}]
            )
        
        return favorite
    
    async def get_favorite_count(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> int:
        """Get favorite count for a user."""
        return await self.repository.get_favorite_count_by_user(db, user_id)
    
    async def get_template_favorite_count(
        self, 
        db: AsyncSession, 
        template_id: int
    ) -> int:
        """Get favorite count for a template."""
        return await self.repository.get_favorite_count_by_template(db, template_id)
    
    async def get_most_favorited_templates(
        self, 
        db: AsyncSession, 
        limit: int = 10
    ) -> List[dict]:
        """Get most favorited templates."""
        return await self.repository.get_most_favorited_templates(db, limit)
    
    async def get_recent_favorites(
        self, 
        db: AsyncSession, 
        limit: int = 10
    ) -> List[UserFavorite]:
        """Get recently added favorites."""
        return await self.repository.get_recent_favorites(db, limit)
    
    async def clear_user_favorites(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> int:
        """Clear all favorites for a user."""
        count = await self.repository.clear_user_favorites(db, user_id)
        return count
    
    async def get_favorites_by_template_ids(
        self, 
        db: AsyncSession, 
        user_id: int,
        template_ids: List[int]
    ) -> List[UserFavorite]:
        """Get favorites for specific template IDs."""
        favorites = await self.repository.get_user_favorites(db, user_id)
        return [f for f in favorites if f.template_id in template_ids]
