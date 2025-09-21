from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from ..models.plan import Plan
from ..models.subscription_new import Subscription
from ..models.usage_tracking import UsageTracking
from ..models.billing import Billing


class SubscriptionServiceNew:
    """Enhanced subscription service with plan-based system"""

    @staticmethod
    async def get_user_subscription(
        db: AsyncSession, 
        user_id: UUID
    ) -> Optional[Subscription]:
        """Get user's current active subscription"""
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == 'active')
            .where(
                (Subscription.end_date.is_(None)) | 
                (Subscription.end_date > datetime.utcnow())
            )
            .order_by(Subscription.start_date.desc())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_subscriptions(
        db: AsyncSession, 
        user_id: UUID
    ) -> List[Subscription]:
        """Get all user subscriptions"""
        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.start_date.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def create_subscription(
        db: AsyncSession, 
        user_id: UUID, 
        plan_id: UUID,
        duration_days: int = None
    ) -> Subscription:
        """Create a new subscription for a user"""
        # Deactivate any existing active subscriptions
        await db.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == 'active')
            .values(status='cancelled', updated_at=datetime.utcnow())
        )
        
        subscription = Subscription.create_subscription(
            user_id=str(user_id), 
            plan_id=str(plan_id),
            duration_days=duration_days
        )
        
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

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
    async def check_feature_access(
        db: AsyncSession, 
        user_id: UUID, 
        feature: str
    ) -> bool:
        """Check if user can access a specific feature"""
        subscription = await SubscriptionServiceNew.get_user_subscription(db, user_id)
        
        if not subscription:
            return False
        
        return subscription.can_use_feature(feature)

    @staticmethod
    async def get_feature_usage(
        db: AsyncSession, 
        user_id: UUID, 
        feature: str
    ) -> Dict[str, Any]:
        """Get feature usage information"""
        subscription = await SubscriptionServiceNew.get_user_subscription(db, user_id)
        
        if not subscription or not subscription.plan:
            return {
                'can_use': False,
                'current_usage': 0,
                'limit': 0,
                'remaining': 0
            }
        
        current_usage = subscription.get_usage(feature)
        limit = subscription.plan.get_limit(feature)
        remaining = subscription.get_remaining_usage(feature)
        
        return {
            'can_use': subscription.can_use_feature(feature),
            'current_usage': current_usage,
            'limit': limit,
            'remaining': remaining
        }

    @staticmethod
    async def increment_feature_usage(
        db: AsyncSession, 
        user_id: UUID, 
        feature: str,
        amount: int = 1
    ) -> bool:
        """Increment feature usage for a user"""
        subscription = await SubscriptionServiceNew.get_user_subscription(db, user_id)
        
        if not subscription:
            return False
        
        if not subscription.can_use_feature(feature):
            return False
        
        subscription.increment_usage(feature, amount)
        await db.commit()
        
        return True

    @staticmethod
    async def get_subscription_status(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get comprehensive subscription status"""
        subscription = await SubscriptionServiceNew.get_user_subscription(db, user_id)
        
        if not subscription:
            return {
                'has_subscription': False,
                'status': 'no_subscription',
                'plan': None,
                'features': {}
            }
        
        # Get feature usage for all features
        features = ['file_upload', 'ai_chat', 'contract', 'report', 'token', 'multi_user']
        feature_usage = {}
        
        for feature in features:
            feature_usage[feature] = await SubscriptionServiceNew.get_feature_usage(db, user_id, feature)
        
        return {
            'has_subscription': True,
            'subscription_id': str(subscription.subscription_id),
            'status': subscription.status,
            'is_active': subscription.is_active,
            'is_expired': subscription.is_expired,
            'days_remaining': subscription.days_remaining,
            'plan': {
                'plan_id': str(subscription.plan.plan_id),
                'plan_name': subscription.plan.plan_name,
                'plan_type': subscription.plan.plan_type,
                'price': float(subscription.plan.price),
                'billing_cycle': subscription.plan.billing_cycle
            },
            'features': feature_usage,
            'start_date': subscription.start_date,
            'end_date': subscription.end_date
        }

    @staticmethod
    async def extend_subscription(
        db: AsyncSession, 
        user_id: UUID, 
        days: int
    ) -> Optional[Subscription]:
        """Extend user's subscription"""
        subscription = await SubscriptionServiceNew.get_user_subscription(db, user_id)
        
        if not subscription:
            return None
        
        subscription.extend_subscription(days)
        await db.commit()
        await db.refresh(subscription)
        
        return subscription

    @staticmethod
    async def cancel_subscription(
        db: AsyncSession, 
        user_id: UUID
    ) -> bool:
        """Cancel user's subscription"""
        subscription = await SubscriptionServiceNew.get_user_subscription(db, user_id)
        
        if not subscription:
            return False
        
        subscription.cancel_subscription()
        await db.commit()
        
        return True

    @staticmethod
    async def create_invoice(
        db: AsyncSession, 
        subscription_id: UUID, 
        amount: float, 
        currency: str = 'SAR',
        payment_method: str = None
    ) -> Billing:
        """Create a new invoice"""
        invoice = Billing.create_invoice(
            subscription_id=str(subscription_id),
            amount=amount,
            currency=currency,
            payment_method=payment_method
        )
        
        db.add(invoice)
        await db.commit()
        await db.refresh(invoice)
        
        return invoice

    @staticmethod
    async def get_user_invoices(
        db: AsyncSession, 
        user_id: UUID
    ) -> List[Billing]:
        """Get user's invoices"""
        result = await db.execute(
            select(Billing)
            .join(Subscription, Billing.subscription_id == Subscription.subscription_id)
            .where(Subscription.user_id == user_id)
            .order_by(Billing.invoice_date.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def cleanup_expired_subscriptions(db: AsyncSession) -> int:
        """Mark expired subscriptions as expired"""
        now = datetime.utcnow()
        result = await db.execute(
            update(Subscription)
            .where(Subscription.status == 'active')
            .where(Subscription.end_date < now)
            .values(status='expired', updated_at=now)
        )
        
        await db.commit()
        return result.rowcount

    @staticmethod
    async def get_usage_tracking(
        db: AsyncSession, 
        user_id: UUID
    ) -> List[UsageTracking]:
        """Get user's usage tracking records"""
        result = await db.execute(
            select(UsageTracking)
            .join(Subscription, UsageTracking.subscription_id == Subscription.subscription_id)
            .where(Subscription.user_id == user_id)
            .order_by(UsageTracking.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def reset_usage_tracking(
        db: AsyncSession, 
        subscription_id: UUID
    ) -> int:
        """Reset usage tracking for a subscription"""
        result = await db.execute(
            update(UsageTracking)
            .where(UsageTracking.subscription_id == subscription_id)
            .where(UsageTracking.should_reset() == True)
            .values(used_count=0, last_reset=datetime.utcnow())
        )
        
        await db.commit()
        return result.rowcount
