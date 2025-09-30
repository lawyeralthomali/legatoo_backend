from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, desc
from typing import List, Optional
from ..models.favorite import UserFavorite


class UserFavoriteRepository:
    """Repository for user favorite operations following SOLID principles."""
    
    def __init__(self):
        pass
    
    async def get_by_id(self, db: AsyncSession, favorite_id: int) -> Optional[UserFavorite]:
        """Get favorite by ID with relationships."""
        result = await db.execute(
            select(UserFavorite)
            .options(
                selectinload(UserFavorite.user),
                selectinload(UserFavorite.template)
            )
            .where(UserFavorite.favorite_id == favorite_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_favorites(self, db: AsyncSession, user_id: int) -> List[UserFavorite]:
        """Get all favorites for a user."""
        result = await db.execute(
            select(UserFavorite)
            .options(selectinload(UserFavorite.template))
            .where(UserFavorite.user_id == user_id)
            .order_by(desc(UserFavorite.created_at))
        )
        return result.scalars().all()
    
    async def is_favorite(
        self, 
        db: AsyncSession, 
        user_id: int, 
        template_id: int
    ) -> bool:
        """Check if a template is favorited by a user."""
        result = await db.execute(
            select(UserFavorite)
            .where(
                and_(
                    UserFavorite.user_id == user_id,
                    UserFavorite.template_id == template_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def add_favorite(
        self, 
        db: AsyncSession, 
        user_id: int, 
        template_id: int
    ) -> Optional[UserFavorite]:
        """Add a template to user favorites."""
        # Check if already favorited
        if await self.is_favorite(db, user_id, template_id):
            return None
        
        favorite = UserFavorite(
            user_id=user_id,
            template_id=template_id
        )
        db.add(favorite)
        await db.commit()
        await db.refresh(favorite)
        return favorite
    
    async def remove_favorite(
        self, 
        db: AsyncSession, 
        user_id: int, 
        template_id: int
    ) -> bool:
        """Remove a template from user favorites."""
        result = await db.execute(
            select(UserFavorite)
            .where(
                and_(
                    UserFavorite.user_id == user_id,
                    UserFavorite.template_id == template_id
                )
            )
        )
        favorite = result.scalar_one_or_none()
        
        if favorite:
            await db.delete(favorite)
            await db.commit()
            return True
        return False
    
    async def get_favorite_by_user_and_template(
        self, 
        db: AsyncSession, 
        user_id: int, 
        template_id: int
    ) -> Optional[UserFavorite]:
        """Get favorite by user and template."""
        result = await db.execute(
            select(UserFavorite)
            .options(
                selectinload(UserFavorite.user),
                selectinload(UserFavorite.template)
            )
            .where(
                and_(
                    UserFavorite.user_id == user_id,
                    UserFavorite.template_id == template_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_favorite_count_by_user(self, db: AsyncSession, user_id: int) -> int:
        """Get favorite count for a user."""
        result = await db.execute(
            select(db.func.count(UserFavorite.favorite_id))
            .where(UserFavorite.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def get_favorite_count_by_template(self, db: AsyncSession, template_id: int) -> int:
        """Get favorite count for a template."""
        result = await db.execute(
            select(db.func.count(UserFavorite.favorite_id))
            .where(UserFavorite.template_id == template_id)
        )
        return result.scalar() or 0
    
    async def get_most_favorited_templates(
        self, 
        db: AsyncSession, 
        limit: int = 10
    ) -> List[dict]:
        """Get most favorited templates."""
        result = await db.execute(
            select(
                UserFavorite.template_id,
                db.func.count(UserFavorite.favorite_id).label('favorite_count')
            )
            .group_by(UserFavorite.template_id)
            .order_by(desc('favorite_count'))
            .limit(limit)
        )
        return [
            {"template_id": template_id, "favorite_count": count}
            for template_id, count in result.fetchall()
        ]
    
    async def get_recent_favorites(self, db: AsyncSession, limit: int = 10) -> List[UserFavorite]:
        """Get recently added favorites."""
        result = await db.execute(
            select(UserFavorite)
            .options(
                selectinload(UserFavorite.user),
                selectinload(UserFavorite.template)
            )
            .order_by(desc(UserFavorite.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def clear_user_favorites(self, db: AsyncSession, user_id: int) -> int:
        """Clear all favorites for a user."""
        result = await db.execute(
            select(UserFavorite).where(UserFavorite.user_id == user_id)
        )
        favorites = result.scalars().all()
        
        for favorite in favorites:
            await db.delete(favorite)
        
        await db.commit()
        return len(favorites)
