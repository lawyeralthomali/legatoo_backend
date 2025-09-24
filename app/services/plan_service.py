from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID

from ..models.plan import Plan


class PlanService:
    """Service for managing subscription plans"""
    
    @staticmethod
    async def get_plan(db: AsyncSession, plan_id: UUID) -> Optional[Plan]:
        """Get plan by ID"""
        result = await db.execute(
            select(Plan).where(Plan.plan_id == plan_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_plans(db: AsyncSession, active_only: bool = True) -> List[Plan]:
        """Get all plans"""
        query = select(Plan)
        if active_only:
            query = query.where(Plan.is_active == True)
        
        result = await db.execute(query.order_by(Plan.price))
        return result.scalars().all()
    
    @staticmethod
    async def get_plan_by_type(db: AsyncSession, plan_type: str) -> Optional[Plan]:
        """Get plan by type (free, monthly, annual)"""
        result = await db.execute(
            select(Plan).where(Plan.plan_type == plan_type)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_free_plan(db: AsyncSession) -> Optional[Plan]:
        """Get the free plan"""
        return await PlanService.get_plan_by_type(db, "free")
    
    @staticmethod
    async def validate_plan_exists(db: AsyncSession, plan_id: UUID) -> bool:
        """Validate that a plan exists and is active"""
        plan = await PlanService.get_plan(db, plan_id)
        return plan is not None and plan.is_active
    
    @staticmethod
    async def get_plan_features(db: AsyncSession, plan_id: UUID) -> dict:
        """Get plan features and limits"""
        plan = await PlanService.get_plan(db, plan_id)
        if not plan:
            return {}
        
        return {
            'file_limit': plan.file_limit,
            'ai_message_limit': plan.ai_message_limit,
            'contract_limit': plan.contract_limit,
            'report_limit': plan.report_limit,
            'token_limit': plan.token_limit,
            'multi_user_limit': plan.multi_user_limit,
            'government_integration': plan.government_integration
        }
