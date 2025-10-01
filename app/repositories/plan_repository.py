"""
Plan Repository for data access operations.

This module handles all database operations related to subscription plans,
following the Repository pattern for clean separation of concerns.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from .base import BaseRepository
from ..models.plan import Plan


class PlanRepository(BaseRepository):
    """Repository for plan data access operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize plan repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, Plan)
    
    async def get_by_plan_id(self, plan_id: UUID) -> Optional[Plan]:
        """
        Get plan by plan_id (UUID).
        
        Args:
            plan_id: Plan UUID
            
        Returns:
            Plan if found, None otherwise
        """
        result = await self.db.execute(
            select(Plan).where(Plan.plan_id == plan_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_plans(self, active_only: bool = True) -> List[Plan]:
        """
        Get all plans with optional active filter.
        
        Args:
            active_only: If True, only return active plans
            
        Returns:
            List of Plan models
        """
        query = select(Plan)
        
        if active_only:
            query = query.where(Plan.is_active == True)
        
        query = query.order_by(Plan.price)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_plan_type(self, plan_type: str) -> Optional[Plan]:
        """
        Get plan by type (free, monthly, annual).
        
        Args:
            plan_type: Plan type string
            
        Returns:
            Plan if found, None otherwise
        """
        result = await self.db.execute(
            select(Plan).where(Plan.plan_type == plan_type)
        )
        return result.scalar_one_or_none()
    
    async def get_free_plan(self) -> Optional[Plan]:
        """
        Get the free plan.
        
        Returns:
            Free Plan if found, None otherwise
        """
        return await self.get_by_plan_type("free")
    
    async def get_active_plans_by_type(self, plan_type: str) -> List[Plan]:
        """
        Get active plans by type.
        
        Args:
            plan_type: Plan type string
            
        Returns:
            List of active Plan models matching the type
        """
        result = await self.db.execute(
            select(Plan).where(
                Plan.plan_type == plan_type,
                Plan.is_active == True
            ).order_by(Plan.price)
        )
        return result.scalars().all()
    
    async def is_plan_active(self, plan_id: UUID) -> bool:
        """
        Check if a plan exists and is active.
        
        Args:
            plan_id: Plan UUID
            
        Returns:
            True if plan exists and is active, False otherwise
        """
        plan = await self.get_by_plan_id(plan_id)
        return plan is not None and plan.is_active
    
    async def get_plan_features(self, plan_id: UUID) -> Optional[dict]:
        """
        Get plan features and limits.
        
        Args:
            plan_id: Plan UUID
            
        Returns:
            Dictionary of plan features or None if plan not found
        """
        plan = await self.get_by_plan_id(plan_id)
        
        if not plan:
            return None
        
        return {
            'plan_id': str(plan.plan_id),
            'plan_name': plan.plan_name,
            'plan_type': plan.plan_type,
            'file_limit': plan.file_limit,
            'ai_message_limit': plan.ai_message_limit,
            'contract_limit': plan.contract_limit,
            'report_limit': plan.report_limit,
            'token_limit': plan.token_limit,
            'multi_user_limit': plan.multi_user_limit,
            'government_integration': plan.government_integration,
            'price': float(plan.price) if plan.price else 0.0,
            'is_active': plan.is_active
        }
    
    async def get_plans_ordered_by_price(self, active_only: bool = True) -> List[Plan]:
        """
        Get all plans ordered by price (ascending).
        
        Args:
            active_only: If True, only return active plans
            
        Returns:
            List of Plan models ordered by price
        """
        query = select(Plan)
        
        if active_only:
            query = query.where(Plan.is_active == True)
        
        query = query.order_by(Plan.price.asc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def count_active_plans(self) -> int:
        """
        Count number of active plans.
        
        Returns:
            Number of active plans
        """
        plans = await self.get_all_plans(active_only=True)
        return len(plans)

