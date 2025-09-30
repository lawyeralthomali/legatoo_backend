from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_
from typing import List, Optional
from ..models.contract_category import ContractCategory


class ContractCategoryRepository:
    """Repository for contract category operations following SOLID principles."""
    
    def __init__(self):
        pass
    
    async def get_by_id(self, db: AsyncSession, category_id: int) -> Optional[ContractCategory]:
        """Get category by ID with relationships."""
        result = await db.execute(
            select(ContractCategory)
            .options(selectinload(ContractCategory.children))
            .where(ContractCategory.category_id == category_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_active(self, db: AsyncSession) -> List[ContractCategory]:
        """Get all active categories."""
        result = await db.execute(
            select(ContractCategory)
            .where(ContractCategory.is_active == True)
            .order_by(ContractCategory.sort_order)
        )
        return result.scalars().all()
    
    async def get_by_parent_id(self, db: AsyncSession, parent_id: Optional[int] = None) -> List[ContractCategory]:
        """Get categories by parent ID (None for root categories)."""
        query = select(ContractCategory).where(ContractCategory.is_active == True)
        
        if parent_id is None:
            query = query.where(ContractCategory.parent_id.is_(None))
        else:
            query = query.where(ContractCategory.parent_id == parent_id)
        
        query = query.order_by(ContractCategory.sort_order)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_children(self, db: AsyncSession, parent_id: int) -> List[ContractCategory]:
        """Get all children of a category."""
        result = await db.execute(
            select(ContractCategory)
            .where(
                and_(
                    ContractCategory.parent_id == parent_id,
                    ContractCategory.is_active == True
                )
            )
            .order_by(ContractCategory.sort_order)
        )
        return result.scalars().all()
    
    async def search_by_name(self, db: AsyncSession, search_term: str) -> List[ContractCategory]:
        """Search categories by name (Arabic or English)."""
        result = await db.execute(
            select(ContractCategory)
            .where(
                and_(
                    ContractCategory.is_active == True,
                    or_(
                        ContractCategory.name_ar.ilike(f"%{search_term}%"),
                        ContractCategory.name_en.ilike(f"%{search_term}%")
                    )
                )
            )
            .order_by(ContractCategory.sort_order)
        )
        return result.scalars().all()
    
    async def get_by_legal_field(self, db: AsyncSession, legal_field: str) -> List[ContractCategory]:
        """Get categories by legal field."""
        result = await db.execute(
            select(ContractCategory)
            .where(
                and_(
                    ContractCategory.legal_field == legal_field,
                    ContractCategory.is_active == True
                )
            )
            .order_by(ContractCategory.sort_order)
        )
        return result.scalars().all()
    
    async def get_by_business_scope(self, db: AsyncSession, business_scope: str) -> List[ContractCategory]:
        """Get categories by business scope."""
        result = await db.execute(
            select(ContractCategory)
            .where(
                and_(
                    ContractCategory.business_scope == business_scope,
                    ContractCategory.is_active == True
                )
            )
            .order_by(ContractCategory.sort_order)
        )
        return result.scalars().all()
    
    async def get_by_complexity_level(self, db: AsyncSession, complexity_level: str) -> List[ContractCategory]:
        """Get categories by complexity level."""
        result = await db.execute(
            select(ContractCategory)
            .where(
                and_(
                    ContractCategory.complexity_level == complexity_level,
                    ContractCategory.is_active == True
                )
            )
            .order_by(ContractCategory.sort_order)
        )
        return result.scalars().all()
    
    async def soft_delete(self, db: AsyncSession, category_id: int) -> bool:
        """Soft delete a category by setting is_active to False."""
        category = await self.get_by_id(db, category_id)
        if category:
            category.is_active = False
            await db.commit()
            return True
        return False
    
    async def increment_template_count(self, db: AsyncSession, category_id: int) -> bool:
        """Increment template count for a category."""
        category = await self.get_by_id(db, category_id)
        if category:
            category.template_count += 1
            await db.commit()
            return True
        return False
    
    async def increment_usage_count(self, db: AsyncSession, category_id: int) -> bool:
        """Increment usage count for a category."""
        category = await self.get_by_id(db, category_id)
        if category:
            category.usage_count += 1
            await db.commit()
            return True
        return False
