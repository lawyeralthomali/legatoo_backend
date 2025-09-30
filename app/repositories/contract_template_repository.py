from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, desc
from typing import List, Optional
from ..models.template import ContractTemplate


class ContractTemplateRepository:
    """Repository for contract template operations following SOLID principles."""
    
    def __init__(self):
        pass
    
    async def get_by_id(self, db: AsyncSession, template_id: int) -> Optional[ContractTemplate]:
        """Get template by ID with relationships."""
        result = await db.execute(
            select(ContractTemplate)
            .options(selectinload(ContractTemplate.category))
            .where(ContractTemplate.template_id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_active(self, db: AsyncSession) -> List[ContractTemplate]:
        """Get all active templates."""
        result = await db.execute(
            select(ContractTemplate)
            .where(ContractTemplate.is_active == True)
            .order_by(desc(ContractTemplate.usage_count))
        )
        return result.scalars().all()
    
    async def get_by_category_id(self, db: AsyncSession, category_id: int) -> List[ContractTemplate]:
        """Get templates by category ID."""
        result = await db.execute(
            select(ContractTemplate)
            .where(
                and_(
                    ContractTemplate.category_id == category_id,
                    ContractTemplate.is_active == True
                )
            )
            .order_by(desc(ContractTemplate.usage_count))
        )
        return result.scalars().all()
    
    async def search_templates(
        self, 
        db: AsyncSession, 
        search_term: Optional[str] = None,
        category_id: Optional[int] = None,
        is_featured: Optional[bool] = None,
        is_premium: Optional[bool] = None
    ) -> List[ContractTemplate]:
        """Search templates with filters."""
        query = select(ContractTemplate).where(ContractTemplate.is_active == True)
        
        if search_term:
            query = query.where(
                or_(
                    ContractTemplate.title_ar.ilike(f"%{search_term}%"),
                    ContractTemplate.title_en.ilike(f"%{search_term}%"),
                    ContractTemplate.description_ar.ilike(f"%{search_term}%"),
                    ContractTemplate.description_en.ilike(f"%{search_term}%")
                )
            )
        
        if category_id:
            query = query.where(ContractTemplate.category_id == category_id)
        
        if is_featured is not None:
            query = query.where(ContractTemplate.is_featured == is_featured)
        
        if is_premium is not None:
            query = query.where(ContractTemplate.is_premium == is_premium)
        
        query = query.order_by(desc(ContractTemplate.usage_count))
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_featured_templates(self, db: AsyncSession) -> List[ContractTemplate]:
        """Get featured templates."""
        result = await db.execute(
            select(ContractTemplate)
            .where(
                and_(
                    ContractTemplate.is_featured == True,
                    ContractTemplate.is_active == True
                )
            )
            .order_by(desc(ContractTemplate.usage_count))
        )
        return result.scalars().all()
    
    async def get_premium_templates(self, db: AsyncSession) -> List[ContractTemplate]:
        """Get premium templates."""
        result = await db.execute(
            select(ContractTemplate)
            .where(
                and_(
                    ContractTemplate.is_premium == True,
                    ContractTemplate.is_active == True
                )
            )
            .order_by(desc(ContractTemplate.usage_count))
        )
        return result.scalars().all()
    
    async def get_free_templates(self, db: AsyncSession) -> List[ContractTemplate]:
        """Get free templates."""
        result = await db.execute(
            select(ContractTemplate)
            .where(
                and_(
                    ContractTemplate.is_premium == False,
                    ContractTemplate.is_active == True
                )
            )
            .order_by(desc(ContractTemplate.usage_count))
        )
        return result.scalars().all()
    
    async def get_by_created_by(self, db: AsyncSession, created_by: int) -> List[ContractTemplate]:
        """Get templates created by a specific user."""
        result = await db.execute(
            select(ContractTemplate)
            .where(
                and_(
                    ContractTemplate.created_by == created_by,
                    ContractTemplate.is_active == True
                )
            )
            .order_by(desc(ContractTemplate.created_at))
        )
        return result.scalars().all()
    
    async def increment_usage_count(self, db: AsyncSession, template_id: int) -> bool:
        """Increment usage count for a template."""
        template = await self.get_by_id(db, template_id)
        if template:
            template.usage_count += 1
            await db.commit()
            return True
        return False
    
    async def update_rating(self, db: AsyncSession, template_id: int, rating: int) -> bool:
        """Update template rating."""
        template = await self.get_by_id(db, template_id)
        if template:
            # Calculate new average rating
            total_rating = template.avg_rating * template.review_count + rating
            template.review_count += 1
            template.avg_rating = total_rating // template.review_count
            await db.commit()
            return True
        return False
    
    async def get_most_used_templates(self, db: AsyncSession, limit: int = 10) -> List[ContractTemplate]:
        """Get most used templates."""
        result = await db.execute(
            select(ContractTemplate)
            .where(ContractTemplate.is_active == True)
            .order_by(desc(ContractTemplate.usage_count))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_recent_templates(self, db: AsyncSession, limit: int = 10) -> List[ContractTemplate]:
        """Get recently created templates."""
        result = await db.execute(
            select(ContractTemplate)
            .where(ContractTemplate.is_active == True)
            .order_by(desc(ContractTemplate.created_at))
            .limit(limit)
        )
        return result.scalars().all()
