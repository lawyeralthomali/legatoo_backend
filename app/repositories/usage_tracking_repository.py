"""
Usage Tracking Repository for data access operations.

This module handles all database operations related to usage tracking,
following the Repository pattern for clean separation of concerns.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from datetime import datetime

from .base import BaseRepository
from ..models.usage_tracking import UsageTracking


class UsageTrackingRepository(BaseRepository):
    """Repository for usage tracking data access operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize usage tracking repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, UsageTracking)
    
    async def get_by_subscription_and_feature(
        self,
        subscription_id: UUID,
        feature: str
    ) -> Optional[UsageTracking]:
        """
        Get usage tracking record for a subscription and feature.
        
        Args:
            subscription_id: Subscription UUID
            feature: Feature name
            
        Returns:
            UsageTracking if found, None otherwise
        """
        result = await self.db.execute(
            select(UsageTracking)
            .where(UsageTracking.subscription_id == subscription_id)
            .where(UsageTracking.feature == feature)
        )
        return result.scalar_one_or_none()
    
    async def create_usage_record(
        self,
        subscription_id: UUID,
        feature: str,
        used_count: int = 1,
        reset_cycle: str = 'monthly'
    ) -> UsageTracking:
        """
        Create a new usage tracking record.
        
        Args:
            subscription_id: Subscription UUID
            feature: Feature name
            used_count: Initial usage count
            reset_cycle: Reset cycle (monthly, annual, etc.)
            
        Returns:
            Created UsageTracking model
        """
        usage_record = UsageTracking(
            subscription_id=subscription_id,
            feature=feature,
            used_count=used_count,
            reset_cycle=reset_cycle
        )
        
        self.db.add(usage_record)
        await self.db.commit()
        await self.db.refresh(usage_record)
        
        return usage_record
    
    async def increment_usage(
        self,
        subscription_id: UUID,
        feature: str,
        amount: int = 1
    ) -> bool:
        """
        Increment usage count for a feature.
        
        Args:
            subscription_id: Subscription UUID
            feature: Feature name
            amount: Amount to increment by
            
        Returns:
            True if incremented, False if record not found
        """
        usage_record = await self.get_by_subscription_and_feature(subscription_id, feature)
        
        if not usage_record:
            return False
        
        usage_record.used_count += amount
        await self.db.commit()
        
        return True
    
    async def get_or_create_usage_record(
        self,
        subscription_id: UUID,
        feature: str
    ) -> UsageTracking:
        """
        Get existing usage record or create new one.
        
        Args:
            subscription_id: Subscription UUID
            feature: Feature name
            
        Returns:
            UsageTracking model
        """
        usage_record = await self.get_by_subscription_and_feature(subscription_id, feature)
        
        if not usage_record:
            usage_record = await self.create_usage_record(
                subscription_id=subscription_id,
                feature=feature,
                used_count=0,
                reset_cycle='monthly'
            )
        
        return usage_record
    
    async def reset_subscription_usage(self, subscription_id: UUID) -> int:
        """
        Reset all usage tracking for a subscription.
        
        Args:
            subscription_id: Subscription UUID
            
        Returns:
            Number of records reset
        """
        result = await self.db.execute(
            update(UsageTracking)
            .where(UsageTracking.subscription_id == subscription_id)
            .values(used_count=0, last_reset=datetime.utcnow())
        )
        
        await self.db.commit()
        return result.rowcount
    
    async def get_user_usage_tracking(self, user_id: UUID) -> List[UsageTracking]:
        """
        Get all usage tracking records for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of UsageTracking models
        """
        from ..models.subscription import Subscription
        
        result = await self.db.execute(
            select(UsageTracking)
            .join(Subscription, UsageTracking.subscription_id == Subscription.subscription_id)
            .where(Subscription.user_id == user_id)
            .order_by(UsageTracking.last_reset.desc())
        )
        return result.scalars().all()

