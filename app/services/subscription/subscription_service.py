from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from ...models.subscription import Subscription, StatusType
from ...models.usage_tracking import UsageTracking
from ...models.billing import Billing
from ...repositories.plan_repository import PlanRepository
from ...repositories.subscription_repository import SubscriptionRepository
from ...repositories.usage_tracking_repository import UsageTrackingRepository
from ...repositories.billing_repository import BillingRepository


class SubscriptionService:
    """
    Enhanced subscription service with plan-based system.
    
    Follows Dependency Inversion Principle by using repository abstractions
    for all data access operations.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize subscription service with repositories.
        
        Args:
            db: Database session
        """
        self.db = db
        self.subscription_repository = SubscriptionRepository(db)
        self.usage_tracking_repository = UsageTrackingRepository(db)
        self.billing_repository = BillingRepository(db)
        self.plan_repository = PlanRepository(db)

    async def get_user_subscription(
        self,
        user_id: UUID
    ) -> Optional[Subscription]:
        """Get user's current active subscription (via repository)."""
        return await self.subscription_repository.get_user_active_subscription(user_id)

    async def get_user_subscriptions(
        self,
        user_id: UUID
    ) -> List[Subscription]:
        """Get all user subscriptions (via repository)."""
        return await self.subscription_repository.get_all_user_subscriptions(user_id)

    async def create_subscription(
        self,
        user_id: UUID, 
        plan_id: UUID,
        duration_days: int = None
    ) -> Subscription:
        """Create a new subscription for a user."""
        # Validate plan exists (via repository)
        if not await self.plan_repository.is_plan_active(plan_id):
            raise ValueError(f"Plan {plan_id} does not exist or is not active")
        
        # Deactivate any existing active subscriptions (via repository)
        await self.subscription_repository.deactivate_user_subscriptions(user_id)
        
        # Create new subscription (via repository)
        return await self.subscription_repository.create_subscription(
            user_id=user_id,
            plan_id=plan_id,
            duration_days=duration_days
        )


    async def check_feature_access(
        self,
        user_id: UUID, 
        feature: str
    ) -> bool:
        """Check if user can access a specific feature."""
        # Get active subscription (via repository)
        subscription = await self.subscription_repository.get_user_active_subscription(user_id)
        
        if not subscription or not subscription.plan:
            return False
        
        # Get usage tracking record (via repository)
        usage_record = await self.usage_tracking_repository.get_by_subscription_and_feature(
            subscription.subscription_id, 
            feature
        )
        
        if not usage_record:
            return True  # No usage record means no limit
        
        # Get plan limit for this feature
        limit = subscription.plan.get_limit(feature)
        if limit == 0:  # Unlimited
            return True
        
        return usage_record.used_count < limit

    async def get_feature_usage(
        self,
        user_id: UUID, 
        feature: str
    ) -> Dict[str, Any]:
        """Get feature usage information."""
        # Get active subscription (via repository)
        subscription = await self.subscription_repository.get_user_active_subscription(user_id)
        
        if not subscription or not subscription.plan:
            return {
                'can_use': False,
                'current_usage': 0,
                'limit': 0,
                'remaining': 0
            }
        
        # Get usage tracking record (via repository)
        usage_record = await self.usage_tracking_repository.get_by_subscription_and_feature(
            subscription.subscription_id,
            feature
        )
        
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

    async def increment_feature_usage(
        self,
        user_id: UUID, 
        feature: str,
        amount: int = 1
    ) -> bool:
        """Increment feature usage for a user."""
        # Get active subscription (via repository)
        subscription = await self.subscription_repository.get_user_active_subscription(user_id)
        
        if not subscription or not subscription.plan:
            return False
        
        # Check if user can use the feature
        can_use = await self.check_feature_access(user_id, feature)
        if not can_use:
            return False
        
        # Get usage record (via repository)
        usage_record = await self.usage_tracking_repository.get_by_subscription_and_feature(
            subscription.subscription_id,
            feature
        )
        
        if not usage_record:
            # Create new usage tracking record (via repository)
            await self.usage_tracking_repository.create_usage_record(
                subscription_id=subscription.subscription_id,
                feature=feature,
                used_count=amount,
                reset_cycle='monthly'
            )
        else:
            # Increment existing usage (via repository)
            await self.usage_tracking_repository.increment_usage(
                subscription.subscription_id,
                feature,
                amount
            )
        
        return True

    async def get_subscription_status(
        self,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get comprehensive subscription status."""
        # Get active subscription (via repository)
        subscription = await self.subscription_repository.get_user_active_subscription(user_id)
        
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
            feature_usage[feature] = await self.get_feature_usage(user_id, feature)
        
        # Get plan information (via repository)
        plan = await self.plan_repository.get_by_plan_id(subscription.plan_id)
        
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

    async def extend_subscription(
        self,
        user_id: UUID, 
        days: int
    ) -> Optional[Subscription]:
        """Extend user's subscription."""
        # Get active subscription (via repository)
        subscription = await self.subscription_repository.get_user_active_subscription(user_id)
        
        if not subscription:
            return None
        
        # Extend subscription (via repository)
        return await self.subscription_repository.extend_subscription(subscription.subscription_id, days)

    async def cancel_subscription(
        self,
        user_id: UUID
    ) -> bool:
        """Cancel user's subscription."""
        # Get active subscription (via repository)
        subscription = await self.subscription_repository.get_user_active_subscription(user_id)
        
        if not subscription:
            return False
        
        # Cancel subscription (via repository)
        return await self.subscription_repository.cancel_subscription(subscription.subscription_id)

    async def create_invoice(
        self,
        subscription_id: UUID, 
        amount: float, 
        currency: str = 'SAR',
        payment_method: str = None
    ) -> Billing:
        """Create a new invoice (via repository)."""
        return await self.billing_repository.create_invoice(
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method
        )

    async def get_user_invoices(
        self,
        user_id: UUID
    ) -> List[Billing]:
        """Get user's invoices (via repository)."""
        return await self.billing_repository.get_user_invoices(user_id)

    async def cleanup_expired_subscriptions(self) -> int:
        """Mark expired subscriptions as expired (via repository)."""
        return await self.subscription_repository.cleanup_expired_subscriptions()

    async def get_usage_tracking(
        self,
        user_id: UUID
    ) -> List[UsageTracking]:
        """Get user's usage tracking records (via repository)."""
        return await self.usage_tracking_repository.get_user_usage_tracking(user_id)

    async def reset_usage_tracking(
        self,
        subscription_id: UUID
    ) -> int:
        """Reset usage tracking for a subscription (via repository)."""
        return await self.usage_tracking_repository.reset_subscription_usage(subscription_id)

    async def validate_plan_for_subscription(
        self,
        plan_id: UUID
    ) -> bool:
        """Validate that a plan exists and is active (via repository)."""
        return await self.plan_repository.is_plan_active(plan_id)

    async def validate_subscription_ownership(
        self,
        user_id: UUID, 
        subscription_id: UUID
    ) -> bool:
        """Validate that a subscription belongs to a user."""
        subscriptions = await self.subscription_repository.get_all_user_subscriptions(user_id)
        subscription_ids = [str(sub.subscription_id) for sub in subscriptions]
        return str(subscription_id) in subscription_ids

    async def validate_feature_usage_request(
        self,
        user_id: UUID, 
        feature: str, 
        amount: int = 1
    ) -> bool:
        """Validate if user can use a feature."""
        return await self.check_feature_access(user_id, feature)

    async def validate_extend_subscription_request(
        self,
        user_id: UUID, 
        days: int
    ) -> bool:
        """Validate extend subscription request."""
        if days <= 0:
            return False
        subscription = await self.subscription_repository.get_user_active_subscription(user_id)
        return subscription is not None
