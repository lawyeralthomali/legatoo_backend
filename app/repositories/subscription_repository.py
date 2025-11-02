"""
Subscription Repository for data access operations.

This module handles all database operations related to subscriptions,
following the Repository pattern for clean separation of concerns.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime

from .base import BaseRepository
from ..models.subscription import Subscription, StatusType


class SubscriptionRepository(BaseRepository):
    """Repository for subscription data access operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize subscription repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, Subscription)
    
    async def get_user_active_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """
        Get user's current active subscription.
        
        Args:
            user_id: User UUID
            
        Returns:
            Active Subscription if found, None otherwise
        """
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == StatusType.ACTIVE)
            .where(
                (Subscription.end_date.is_(None)) | 
                (Subscription.end_date > datetime.utcnow())
            )
            .order_by(Subscription.start_date.desc())
        )
        return result.scalar_one_or_none()
    
    async def get_all_user_subscriptions(self, user_id: UUID) -> List[Subscription]:
        """
        Get all subscriptions for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            List of Subscription models
        """
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.start_date.desc())
        )
        return result.scalars().all()
    
    async def create_subscription(
        self,
        user_id: UUID,
        plan_id: UUID,
        duration_days: Optional[int] = None
    ) -> Subscription:
        """
        Create a new subscription.
        
        Args:
            user_id: User UUID
            plan_id: Plan UUID
            duration_days: Optional duration in days
            
        Returns:
            Created Subscription model
        """
        subscription = Subscription.create_subscription(
            user_id=str(user_id), 
            plan_id=str(plan_id),
            duration_days=duration_days
        )
        
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        return subscription
    
    async def deactivate_user_subscriptions(self, user_id: UUID) -> int:
        """
        Deactivate all active subscriptions for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Number of subscriptions deactivated
        """
        result = await self.db.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == StatusType.ACTIVE)
            .values(status=StatusType.CANCELLED, updated_at=datetime.utcnow())
        )
        
        await self.db.commit()
        return result.rowcount
    
    async def extend_subscription(
        self,
        subscription_id: UUID,
        days: int
    ) -> Optional[Subscription]:
        """
        Extend a subscription by days.
        
        Args:
            subscription_id: Subscription UUID
            days: Number of days to extend
            
        Returns:
            Updated Subscription or None if not found
        """
        result = await self.db.execute(
            select(Subscription).where(Subscription.subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return None
        
        subscription.extend_subscription(days)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        return subscription
    
    async def cancel_subscription(self, subscription_id: UUID) -> bool:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Subscription UUID
            
        Returns:
            True if cancelled, False if not found
        """
        result = await self.db.execute(
            select(Subscription).where(Subscription.subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return False
        
        subscription.cancel_subscription()
        await self.db.commit()
        
        return True
    
    async def cleanup_expired_subscriptions(self) -> int:
        """
        Mark expired subscriptions as expired.
        
        Returns:
            Number of subscriptions marked as expired
        """
        now = datetime.utcnow()
        result = await self.db.execute(
            update(Subscription)
            .where(Subscription.status == StatusType.ACTIVE)
            .where(Subscription.end_date < now)
            .values(status=StatusType.EXPIRED, updated_at=now)
        )
        
        await self.db.commit()
        return result.rowcount
    
    async def get_subscription_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        """
        Get subscription by ID.
        
        Args:
            subscription_id: Subscription UUID
            
        Returns:
            Subscription if found, None otherwise
        """
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.subscription_id == subscription_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_subscribers_with_details(self, skip: int = 0, limit: int = 100) -> List[Subscription]:
        """
        Get all subscriptions with profile and plan details.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Subscription models with loaded relationships
        """
        from ..models.profile import Profile
        
        result = await self.db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.profile)
            )
            .join(Profile, Subscription.user_id == Profile.id)
            .order_by(Subscription.start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_subscriber_by_subscription_id(self, subscription_id: UUID) -> Optional[Subscription]:
        """
        Get subscription with profile and plan details by subscription ID.
        
        Args:
            subscription_id: Subscription UUID
            
        Returns:
            Subscription with loaded relationships if found, None otherwise
        """
        result = await self.db.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.profile)
            )
            .where(Subscription.subscription_id == subscription_id)
        )
        return result.scalar_one_or_none()

