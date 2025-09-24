from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID

from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
from ..utils.subscription import get_subscription_status
from ..services.subscription_service import SubscriptionServiceNew
from ..models.plan import Plan
from ..models.subscription import Subscription
from ..models.billing import Billing
from ..schemas.subscription import (
    SubscriptionResponse, 
    SubscriptionStatusResponse,
    PlanResponse,
    BillingResponse,
    FeatureUsageResponse,
    UsageTrackingResponse
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


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
    db: AsyncSession = Depends(get_db)
):
    """Get all available subscription plans"""
    plans = await SubscriptionServiceNew.get_plans(db, active_only=active_only)
    
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
    db: AsyncSession = Depends(get_db)
):
    """Subscribe to a plan"""
    # Check if plan exists
    plan = await SubscriptionServiceNew.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    if not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan is not active"
        )
    
    # Create subscription
    subscription = await SubscriptionServiceNew.create_subscription(
        db=db,
        user_id=current_user.sub,
        plan_id=plan_id,
        duration_days=duration_days
    )
    
    return {
        "subscription_id": str(subscription.subscription_id),
        "plan_name": plan.plan_name,
        "plan_type": plan.plan_type,
        "price": float(plan.price),
        "billing_cycle": plan.billing_cycle,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
        "status": subscription.status
    }


@router.get("/my-subscriptions", response_model=List[Dict[str, Any]])
async def get_my_subscriptions(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's all subscriptions"""
    subscriptions = await SubscriptionServiceNew.get_user_subscriptions(db, current_user.sub)
    
    return [
        {
            "subscription_id": str(sub.subscription_id),
            "plan_name": sub.plan.plan_name,
            "plan_type": sub.plan.plan_type,
            "price": float(sub.plan.price),
            "billing_cycle": sub.plan.billing_cycle,
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
    db: AsyncSession = Depends(get_db)
):
    """Get feature usage information"""
    return await SubscriptionServiceNew.get_feature_usage(db, current_user.sub, feature)


@router.post("/features/{feature}/use")
async def use_feature(
    feature: str,
    amount: int = 1,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Use a feature (increment usage)"""
    success = await SubscriptionServiceNew.increment_feature_usage(
        db=db,
        user_id=current_user.sub,
        feature=feature,
        amount=amount
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot use feature '{feature}'. Check your subscription limits."
        )
    
    return {"message": f"Successfully used {amount} {feature}(s)"}


@router.put("/extend")
async def extend_subscription(
    days: int,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Extend current subscription"""
    if days <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be greater than 0"
        )
    
    subscription = await SubscriptionServiceNew.extend_subscription(
        db=db,
        user_id=current_user.sub,
        days=days
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return {
        "message": f"Subscription extended by {days} days",
        "new_end_date": subscription.end_date,
        "days_remaining": subscription.days_remaining
    }


@router.put("/cancel")
async def cancel_subscription(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel current subscription"""
    success = await SubscriptionServiceNew.cancel_subscription(
        db=db,
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
    db: AsyncSession = Depends(get_db)
):
    """Get current user's invoices"""
    invoices = await SubscriptionServiceNew.get_user_invoices(db, current_user.sub)
    
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
    db: AsyncSession = Depends(get_db)
):
    """Create a new invoice"""
    # Verify subscription belongs to user
    subscription = await SubscriptionServiceNew.get_user_subscriptions(db, current_user.sub)
    subscription_ids = [str(sub.subscription_id) for sub in subscription]
    
    if str(subscription_id) not in subscription_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription not found or access denied"
        )
    
    invoice = await SubscriptionServiceNew.create_invoice(
        db=db,
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
    db: AsyncSession = Depends(get_db)
):
    """Get usage tracking information"""
    usage_records = await SubscriptionServiceNew.get_usage_tracking(db, current_user.sub)
    
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
    db: AsyncSession = Depends(get_db)
):
    """Clean up expired subscriptions (admin endpoint)"""
    count = await SubscriptionServiceNew.cleanup_expired_subscriptions(db)
    return {"message": f"Cleaned up {count} expired subscriptions"}


@router.get("/admin/usage-stats")
async def get_usage_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics (admin endpoint)"""
    # This would typically require admin authentication
    # For now, just return a placeholder
    return {"message": "Usage statistics endpoint - requires admin authentication"}
