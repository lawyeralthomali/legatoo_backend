from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from ..models.plan import Plan
from ..repositories.plan_repository import PlanRepository


class PlanService:
    """
    Service for managing subscription plans.
    
    Follows Dependency Inversion Principle by using repository abstraction
    for all data access operations.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize plan service with repository.
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = PlanRepository(db)
    
    async def get_plan(self, plan_id: UUID) -> Optional[Plan]:
        """
        Get plan by ID.
        
        Args:
            plan_id: Plan UUID
            
        Returns:
            Plan if found, None otherwise
        """
        return await self.repository.get_by_plan_id(plan_id)
    
    async def get_plans(self, active_only: bool = True) -> List[Plan]:
        """
        Get all plans with optional active filter.
        
        Args:
            active_only: If True, only return active plans
            
        Returns:
            List of Plan models
        """
        return await self.repository.get_all_plans(active_only)
    
    async def get_plan_by_type(self, plan_type: str) -> Optional[Plan]:
        """
        Get plan by type (free, monthly, annual).
        
        Args:
            plan_type: Plan type string
            
        Returns:
            Plan if found, None otherwise
        """
        return await self.repository.get_by_plan_type(plan_type)
    
    async def get_free_plan(self) -> Optional[Plan]:
        """
        Get the free plan.
        
        Returns:
            Free Plan if found, None otherwise
        """
        return await self.repository.get_free_plan()
    
    async def validate_plan_exists(self, plan_id: UUID) -> bool:
        """
        Validate that a plan exists and is active.
        
        Args:
            plan_id: Plan UUID
            
        Returns:
            True if plan exists and is active, False otherwise
        """
        return await self.repository.is_plan_active(plan_id)
    
    async def get_plan_features(self, plan_id: UUID) -> dict:
        """
        Get plan features and limits.
        
        Args:
            plan_id: Plan UUID
            
        Returns:
            Dictionary of plan features, empty dict if plan not found
        """
        features = await self.repository.get_plan_features(plan_id)
        return features if features else {}
