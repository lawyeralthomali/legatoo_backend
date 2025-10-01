from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID
from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
from ..utils.subscription import get_subscription_status
from ..services.subscription_service import SubscriptionService
from ..services.plan_service import PlanService
from fastapi import HTTPException, status


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def get_plan_service(db: AsyncSession = Depends(get_db)) -> PlanService:
    """Dependency to get plan service."""
    return PlanService(db)


def get_subscription_service(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    """Dependency to get subscription service."""
    return SubscriptionService(db)


@router.get("/status", response_model=Dict[str, Any])
async def get_my_subscription_status(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's subscription status"""
    return await get_subscription_status(current_user, db)


@router.get("/plans", response_model=List[Dict[str, Any]])
async def get_available_plans(
    active_only: bool = True,
    plan_service: PlanService = Depends(get_plan_service)
):
    """Get all available subscription plans"""
    plans = await plan_service.get_plans(active_only=active_only)
    return [
        {
            "plan_id": str(plan.plan_id),
            "plan_name": plan.plan_name,
            "plan_type": plan.plan_type,
            "price": float(plan.price),
            "billing_cycle": plan.billing_cycle,
            "file_limit": plan.file_limit,
            "ai_message_limit": plan.ai_message_limit,
            "contract_limit": plan.contract_limit,
            "report_limit": plan.report_limit,
            "token_limit": plan.token_limit,
            "multi_user_limit": plan.multi_user_limit,
            "government_integration": plan.government_integration,
            "description": plan.description,
            "is_active": plan.is_active
        }
        for plan in plans
    ]


@router.post("/subscribe", response_model=Dict[str, Any])
async def subscribe_to_plan(
    plan_id: UUID,
    duration_days: int = None,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Subscribe to a plan"""
    # Validate plan exists and is active
    if not await subscription_service.validate_plan_for_subscription(plan_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan not found or not active"
        )
    
    # Create subscription
    subscription = await subscription_service.create_subscription(
        user_id=current_user.sub,
        plan_id=plan_id,
        duration_days=duration_days
    )
    
    return {
        "subscription_id": str(subscription.subscription_id),
        "plan_id": str(subscription.plan_id),
        "plan_name": subscription.plan.plan_name if subscription.plan else None,
        "plan_type": subscription.plan.plan_type if subscription.plan else None,
        "price": float(subscription.plan.price) if subscription.plan else 0,
        "billing_cycle": subscription.plan.billing_cycle if subscription.plan else None,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
        "status": subscription.status
    }


@router.get("/my-subscriptions", response_model=List[Dict[str, Any]])
async def get_my_subscriptions(
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Get current user's all subscriptions"""
    subscriptions = await subscription_service.get_user_subscriptions(current_user.sub)
    return [
        {
            "subscription_id": str(sub.subscription_id),
            "plan_name": sub.plan.plan_name if sub.plan else None,
            "plan_type": sub.plan.plan_type if sub.plan else None,
            "price": float(sub.plan.price) if sub.plan else 0,
            "billing_cycle": sub.plan.billing_cycle if sub.plan else None,
            "start_date": sub.start_date,
            "end_date": sub.end_date,
            "status": sub.status,
            "is_active": sub.is_active,
            "days_remaining": sub.days_remaining,
            "current_usage": sub.current_usage
        }
        for sub in subscriptions
    ]


@router.get("/features/{feature}", response_model=Dict[str, Any])
async def get_feature_usage(
    feature: str,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Get feature usage information"""
    return await subscription_service.get_feature_usage(current_user.sub, feature)


@router.post("/features/{feature}/use")
async def use_feature(
    feature: str,
    amount: int = 1,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Use a feature (increment usage)"""
    # Validate feature usage
    if not await subscription_service.validate_feature_usage_request(current_user.sub, feature, amount):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot use feature '{feature}'. Check your subscription limits."
        )
    
    # Increment usage
    success = await subscription_service.increment_feature_usage(
        user_id=current_user.sub,
        feature=feature,
        amount=amount
    )
    
    return {"message": f"Successfully used {amount} {feature}(s)"}


@router.put("/extend")
async def extend_subscription(
    days: int,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Extend current subscription"""
    # Validate extend request
    if not await subscription_service.validate_extend_subscription_request(current_user.sub, days):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid extend request or no active subscription found"
        )
    
    # Extend subscription
    subscription = await subscription_service.extend_subscription(
        user_id=current_user.sub,
        days=days
    )
    
    return {
        "message": f"Subscription extended by {days} days",
        "new_end_date": subscription.end_date,
        "days_remaining": subscription.days_remaining
    }


@router.put("/cancel")
async def cancel_subscription(
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Cancel current subscription"""
    # Cancel subscription
    success = await subscription_service.cancel_subscription(
        user_id=current_user.sub
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return {"message": "Subscription cancelled successfully"}


@router.get("/invoices", response_model=List[Dict[str, Any]])
async def get_my_invoices(
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Get current user's invoices"""
    invoices = await subscription_service.get_user_invoices(current_user.sub)
    return [
        {
            "invoice_id": str(invoice.invoice_id),
            "amount": float(invoice.amount),
            "currency": invoice.currency,
            "status": invoice.status,
            "invoice_date": invoice.invoice_date,
            "payment_method": invoice.payment_method
        }
        for invoice in invoices
    ]


@router.post("/invoices", response_model=Dict[str, Any])
async def create_invoice(
    subscription_id: UUID,
    amount: float,
    currency: str = "SAR",
    payment_method: str = None,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Create a new invoice"""
    # Validate subscription ownership
    if not await subscription_service.validate_subscription_ownership(current_user.sub, subscription_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription not found or access denied"
        )
    
    # Create invoice
    invoice = await subscription_service.create_invoice(
        subscription_id=subscription_id,
        amount=amount,
        currency=currency,
        payment_method=payment_method
    )
    
    return {
        "invoice_id": str(invoice.invoice_id),
        "amount": float(invoice.amount),
        "currency": invoice.currency,
        "status": invoice.status,
        "invoice_date": invoice.invoice_date,
        "payment_method": invoice.payment_method
    }


@router.get("/usage-tracking", response_model=List[Dict[str, Any]])
async def get_usage_tracking(
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Get usage tracking information"""
    usage_records = await subscription_service.get_usage_tracking(current_user.sub)
    return [
        {
            "usage_id": str(record.usage_id),
            "feature": record.feature,
            "used_count": record.used_count,
            "reset_cycle": record.reset_cycle,
            "last_reset": record.last_reset
        }
        for record in usage_records
    ]


# Admin endpoints
@router.post("/admin/cleanup-expired")
async def cleanup_expired_subscriptions(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """Clean up expired subscriptions (admin endpoint)"""
    count = await subscription_service.cleanup_expired_subscriptions()
    return {"message": f"Cleaned up {count} expired subscriptions"}


@router.get("/admin/usage-stats")
async def get_usage_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics (admin endpoint)"""
    # This would typically require admin authentication
    # For now, just return a placeholder
    return {"message": "Usage statistics endpoint - requires admin authentication"}
