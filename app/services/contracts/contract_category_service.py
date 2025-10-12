from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ...repositories.contract_category_repository import ContractCategoryRepository
from ...models.contract_category import ContractCategory
from ...schemas.category import CategoryCreate, CategoryUpdate
from ...utils.api_exceptions import ApiException


class ContractCategoryService:
    """Service for contract category business logic following SOLID principles."""
    
    def __init__(self):
        self.repository = ContractCategoryRepository()
    
    async def get_categories(
        self, 
        db: AsyncSession, 
        parent_id: Optional[int] = None,
        is_active: bool = True
    ) -> List[ContractCategory]:
        """Get categories with optional filtering."""
        if parent_id is not None:
            return await self.repository.get_by_parent_id(db, parent_id)
        else:
            return await self.repository.get_by_parent_id(db, None)
    
    async def get_category_by_id(
        self, 
        db: AsyncSession, 
        category_id: int
    ) -> ContractCategory:
        """Get category by ID with validation."""
        category = await self.repository.get_by_id(db, category_id)
        if not category:
            raise ApiException(
                status_code=404,
                message="Category not found",
                errors=[{"field": "category_id", "message": "Category does not exist"}]
            )
        return category
    
    async def create_category(
        self, 
        db: AsyncSession, 
        category_data: CategoryCreate
    ) -> ContractCategory:
        """Create a new category with validation."""
        # Validate parent category if specified
        if category_data.parent_id:
            parent_category = await self.repository.get_by_id(db, category_data.parent_id)
            if not parent_category:
                raise ApiException(
                    status_code=400,
                    message="Parent category not found",
                    errors=[{"field": "parent_id", "message": "Parent category does not exist"}]
                )
        
        # Create category
        category = ContractCategory(**category_data.dict())
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category
    
    async def update_category(
        self, 
        db: AsyncSession, 
        category_id: int, 
        update_data: CategoryUpdate
    ) -> ContractCategory:
        """Update category with validation."""
        category = await self.get_category_by_id(db, category_id)
        
        # Validate parent category if being updated
        if update_data.parent_id is not None and update_data.parent_id != category.parent_id:
            if update_data.parent_id == category_id:
                raise ApiException(
                    status_code=400,
                    message="Category cannot be its own parent",
                    errors=[{"field": "parent_id", "message": "Circular reference not allowed"}]
                )
            
            parent_category = await self.repository.get_by_id(db, update_data.parent_id)
            if not parent_category:
                raise ApiException(
                    status_code=400,
                    message="Parent category not found",
                    errors=[{"field": "parent_id", "message": "Parent category does not exist"}]
                )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(category, field, value)
        
        await db.commit()
        await db.refresh(category)
        return category
    
    async def delete_category(
        self, 
        db: AsyncSession, 
        category_id: int
    ) -> bool:
        """Soft delete a category."""
        category = await self.get_category_by_id(db, category_id)
        
        # Check if category has children
        children = await self.repository.get_children(db, category_id)
        if children:
            raise ApiException(
                status_code=400,
                message="Cannot delete category with children",
                errors=[{"field": "category_id", "message": "Category has child categories"}]
            )
        
        return await self.repository.soft_delete(db, category_id)
    
    async def search_categories(
        self, 
        db: AsyncSession, 
        search_term: str
    ) -> List[ContractCategory]:
        """Search categories by name."""
        if not search_term.strip():
            return []
        
        return await self.repository.search_by_name(db, search_term.strip())
    
    async def get_categories_by_legal_field(
        self, 
        db: AsyncSession, 
        legal_field: str
    ) -> List[ContractCategory]:
        """Get categories by legal field."""
        return await self.repository.get_by_legal_field(db, legal_field)
    
    async def get_categories_by_business_scope(
        self, 
        db: AsyncSession, 
        business_scope: str
    ) -> List[ContractCategory]:
        """Get categories by business scope."""
        return await self.repository.get_by_business_scope(db, business_scope)
    
    async def get_categories_by_complexity(
        self, 
        db: AsyncSession, 
        complexity_level: str
    ) -> List[ContractCategory]:
        """Get categories by complexity level."""
        return await self.repository.get_by_complexity_level(db, complexity_level)
    
    async def get_category_hierarchy(
        self, 
        db: AsyncSession
    ) -> List[ContractCategory]:
        """Get complete category hierarchy."""
        # Get all root categories
        root_categories = await self.repository.get_by_parent_id(db, None)
        
        # For each root category, get its children
        for category in root_categories:
            category.children = await self.repository.get_children(db, category.category_id)
        
        return root_categories
    
    async def increment_template_count(
        self, 
        db: AsyncSession, 
        category_id: int
    ) -> bool:
        """Increment template count for a category."""
        return await self.repository.increment_template_count(db, category_id)
    
    async def increment_usage_count(
        self, 
        db: AsyncSession, 
        category_id: int
    ) -> bool:
        """Increment usage count for a category."""
        return await self.repository.increment_usage_count(db, category_id)
