from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from ..models.subscription import Subscription, StatusType
from ..models.usage_tracking import UsageTracking
from ..models.billing import Billing
from .plan_service import PlanService


class SubscriptionService:
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
            .where(Subscription.status == StatusType.ACTIVE)
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
        # Validate plan exists
        if not await PlanService.validate_plan_exists(db, plan_id):
            raise ValueError(f"Plan {plan_id} does not exist or is not active")
        
        # Deactivate any existing active subscriptions
        await db.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == StatusType.ACTIVE)
            .values(status=StatusType.CANCELLED, updated_at=datetime.utcnow())
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
    async def check_feature_access(
        db: AsyncSession, 
        user_id: UUID, 
        feature: str
    ) -> bool:
        """Check if user can access a specific feature"""
        subscription = await SubscriptionService.get_user_subscription(db, user_id)
        
        if not subscription or not subscription.plan:
            return False
        
        # Get usage tracking record for this feature
        result = await db.execute(
            select(UsageTracking)
            .where(UsageTracking.subscription_id == subscription.subscription_id)
            .where(UsageTracking.feature == feature)
        )
        usage_record = result.scalar_one_or_none()
        
        if not usage_record:
            return True  # No usage record means no limit
        
        # Get plan limit for this feature
        limit = subscription.plan.get_limit(feature)
        if limit == 0:  # Unlimited
            return True
        
        return usage_record.used_count < limit

    @staticmethod
    async def get_feature_usage(
        db: AsyncSession, 
        user_id: UUID, 
        feature: str
    ) -> Dict[str, Any]:
        """Get feature usage information"""
        subscription = await SubscriptionService.get_user_subscription(db, user_id)
        
        if not subscription or not subscription.plan:
            return {
                'can_use': False,
                'current_usage': 0,
                'limit': 0,
                'remaining': 0
            }
        
        # Get usage tracking record for this feature
        result = await db.execute(
            select(UsageTracking)
            .where(UsageTracking.subscription_id == subscription.subscription_id)
            .where(UsageTracking.feature == feature)
        )
        usage_record = result.scalar_one_or_none()
        
        current_usage = usage_record.used_count if usage_record else 0
        limit = subscription.plan.get_limit(feature)
        remaining = max(0, limit - current_usage) if limit > 0 else 999999
        can_use = limit == 0 or current_usage < limit
        
        return {
            'can_use': can_use,
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
        subscription = await SubscriptionService.get_user_subscription(db, user_id)
        
        if not subscription or not subscription.plan:
            return False
        
        # Check if user can use the feature
        can_use = await SubscriptionService.check_feature_access(db, user_id, feature)
        if not can_use:
            return False
        
        # Get or create usage tracking record
        result = await db.execute(
            select(UsageTracking)
            .where(UsageTracking.subscription_id == subscription.subscription_id)
            .where(UsageTracking.feature == feature)
        )
        usage_record = result.scalar_one_or_none()
        
        if not usage_record:
            # Create new usage tracking record
            usage_record = UsageTracking(
                subscription_id=subscription.subscription_id,
                feature=feature,
                used_count=amount,
                reset_cycle='monthly'  # Default reset cycle
            )
            db.add(usage_record)
        else:
            # Increment existing usage
            usage_record.used_count += amount
        
        await db.commit()
        return True

    @staticmethod
    async def get_subscription_status(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get comprehensive subscription status"""
        subscription = await SubscriptionService.get_user_subscription(db, user_id)
        
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
            feature_usage[feature] = await SubscriptionService.get_feature_usage(db, user_id, feature)
        
        # Get plan information using PlanService
        plan = await PlanService.get_plan(db, subscription.plan_id)
        
        return {
            'has_subscription': True,
            'subscription_id': str(subscription.subscription_id),
            'status': subscription.status,
            'is_active': subscription.is_active,
            'is_expired': subscription.is_expired,
            'days_remaining': subscription.days_remaining,
            'plan': {
                'plan_id': str(plan.plan_id),
                'plan_name': plan.plan_name,
                'plan_type': plan.plan_type,
                'price': float(plan.price),
                'billing_cycle': plan.billing_cycle
            } if plan else None,
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
        subscription = await SubscriptionService.get_user_subscription(db, user_id)
        
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
        subscription = await SubscriptionService.get_user_subscription(db, user_id)
        
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
            .where(Subscription.status == StatusType.ACTIVE)
            .where(Subscription.end_date < now)
            .values(status=StatusType.EXPIRED, updated_at=now)
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
            .order_by(UsageTracking.last_reset.desc())
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
            .values(used_count=0, last_reset=datetime.utcnow())
        )
        
        await db.commit()
        return result.rowcount

    @staticmethod
    async def validate_plan_for_subscription(
        db: AsyncSession, 
        plan_id: UUID
    ) -> bool:
        """Validate that a plan exists and is active for subscription creation"""
        plan = await PlanService.get_plan(db, plan_id)
        return plan is not None and plan.is_active

    @staticmethod
    async def validate_subscription_ownership(
        db: AsyncSession, 
        user_id: UUID, 
        subscription_id: UUID
    ) -> bool:
        """Validate that a subscription belongs to a user"""
        subscriptions = await SubscriptionService.get_user_subscriptions(db, user_id)
        subscription_ids = [str(sub.subscription_id) for sub in subscriptions]
        return str(subscription_id) in subscription_ids

    @staticmethod
    async def validate_feature_usage_request(
        db: AsyncSession, 
        user_id: UUID, 
        feature: str, 
        amount: int = 1
    ) -> bool:
        """Validate if user can use a feature"""
        return await SubscriptionService.check_feature_access(db, user_id, feature)

    @staticmethod
    async def validate_extend_subscription_request(
        db: AsyncSession, 
        user_id: UUID, 
        days: int
    ) -> bool:
        """Validate extend subscription request"""
        if days <= 0:
            return False
        subscription = await SubscriptionService.get_user_subscription(db, user_id)
        return subscription is not None
