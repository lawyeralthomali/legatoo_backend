from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from uuid import UUID
from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
from ..utils.subscription import get_subscription_status
from ..services.subscription.subscription_service import SubscriptionService
from ..services.subscription.plan_service import PlanService
from fastapi import HTTPException, status
from ..schemas.response import (
    ApiResponse, ErrorDetail,
    create_success_response, create_error_response, create_not_found_response
)


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def get_plan_service(db: AsyncSession = Depends(get_db)) -> PlanService:
    """Dependency to get plan service."""
    return PlanService(db)


def get_subscription_service(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    """Dependency to get subscription service."""
    return SubscriptionService(db)


@router.get("/status", response_model=ApiResponse)
async def get_my_subscription_status(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get current user's subscription status"""
    try:
        status_data = await get_subscription_status(current_user, db)
        return create_success_response(
            message="Subscription status retrieved successfully",
            data=status_data
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve subscription status",
            errors=[ErrorDetail(field="subscription", message=f"Internal server error: {str(e)}")]
        )


@router.get("/plans", response_model=ApiResponse)
async def get_available_plans(
    active_only: bool = True,
    plan_service: PlanService = Depends(get_plan_service)
) -> ApiResponse:
    """Get all available subscription plans"""
    try:
        plans = await plan_service.get_plans(active_only=active_only)
        plans_data = [
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
        return create_success_response(
            message="Plans retrieved successfully",
            data={"plans": plans_data}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve plans",
            errors=[ErrorDetail(field="plans", message=f"Internal server error: {str(e)}")]
        )


@router.post("/subscribe", response_model=ApiResponse)
async def subscribe_to_plan(
    plan_id: UUID,
    duration_days: int = None,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Subscribe to a plan"""
    try:
        # Validate plan exists and is active
        if not await subscription_service.validate_plan_for_subscription(plan_id):
            return create_error_response(
                message="Plan not found or not active",
                errors=[ErrorDetail(field="plan_id", message="The specified plan is not available for subscription")]
            )
        
        # Create subscription
        subscription = await subscription_service.create_subscription(
            user_id=current_user.sub,
            plan_id=plan_id,
            duration_days=duration_days
        )
        
        subscription_data = {
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
        
        return create_success_response(
            message="Successfully subscribed to plan",
            data=subscription_data
        )
    except Exception as e:
        return create_error_response(
            message="Failed to subscribe to plan",
            errors=[ErrorDetail(field="subscription", message=f"Internal server error: {str(e)}")]
        )


@router.get("/my-subscriptions", response_model=ApiResponse)
async def get_my_subscriptions(
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Get current user's all subscriptions"""
    try:
        subscriptions = await subscription_service.get_user_subscriptions(current_user.sub)
        subscriptions_data = [
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
        return create_success_response(
            message="Subscriptions retrieved successfully",
            data={"subscriptions": subscriptions_data}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve subscriptions",
            errors=[ErrorDetail(field="subscriptions", message=f"Internal server error: {str(e)}")]
        )


@router.get("/features/{feature}", response_model=ApiResponse)
async def get_feature_usage(
    feature: str,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Get feature usage information"""
    try:
        usage_data = await subscription_service.get_feature_usage(current_user.sub, feature)
        return create_success_response(
            message="Feature usage retrieved successfully",
            data=usage_data
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve feature usage",
            errors=[ErrorDetail(field="feature", message=f"Internal server error: {str(e)}")]
        )


@router.post("/features/{feature}/use", response_model=ApiResponse)
async def use_feature(
    feature: str,
    amount: int = 1,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Use a feature (increment usage)"""
    try:
        # Validate feature usage
        if not await subscription_service.validate_feature_usage_request(current_user.sub, feature, amount):
            return create_error_response(
                message=f"Cannot use feature '{feature}'. Check your subscription limits.",
                errors=[ErrorDetail(field="feature", message=f"Insufficient quota for {feature}")]
            )
        
        # Increment usage
        success = await subscription_service.increment_feature_usage(
            user_id=current_user.sub,
            feature=feature,
            amount=amount
        )
        
        return create_success_response(
            message=f"Successfully used {amount} {feature}(s)",
            data={"feature": feature, "amount_used": amount}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to use feature",
            errors=[ErrorDetail(field="feature", message=f"Internal server error: {str(e)}")]
        )


@router.put("/extend", response_model=ApiResponse)
async def extend_subscription(
    days: int,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Extend current subscription"""
    try:
        # Validate extend request
        if not await subscription_service.validate_extend_subscription_request(current_user.sub, days):
            return create_error_response(
                message="Invalid extend request or no active subscription found",
                errors=[ErrorDetail(field="subscription", message="No active subscription found or invalid extend request")]
            )
        
        # Extend subscription
        subscription = await subscription_service.extend_subscription(
            user_id=current_user.sub,
            days=days
        )
        
        return create_success_response(
            message=f"Subscription extended by {days} days",
            data={
                "new_end_date": subscription.end_date,
                "days_remaining": subscription.days_remaining
            }
        )
    except Exception as e:
        return create_error_response(
            message="Failed to extend subscription",
            errors=[ErrorDetail(field="subscription", message=f"Internal server error: {str(e)}")]
        )


@router.put("/cancel", response_model=ApiResponse)
async def cancel_subscription(
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Cancel current subscription"""
    try:
        # Cancel subscription
        success = await subscription_service.cancel_subscription(
            user_id=current_user.sub
        )
        
        if not success:
            return create_not_found_response(
                resource="Active subscription",
                field="subscription"
            )
        
        return create_success_response(
            message="Subscription cancelled successfully",
            data={"cancelled": True}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to cancel subscription",
            errors=[ErrorDetail(field="subscription", message=f"Internal server error: {str(e)}")]
        )


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


@router.post("/invoices", response_model=ApiResponse)
async def create_invoice(
    subscription_id: UUID,
    amount: float,
    currency: str = "SAR",
    payment_method: str = None,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Create a new invoice"""
    try:
        # Validate subscription ownership
        if not await subscription_service.validate_subscription_ownership(current_user.sub, subscription_id):
            return create_error_response(
                message="Subscription not found or access denied",
                errors=[ErrorDetail(field="subscription_id", message="You don't have access to this subscription")]
            )
        
        # Create invoice
        invoice = await subscription_service.create_invoice(
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method
        )
        
        invoice_data = {
            "invoice_id": str(invoice.invoice_id),
            "amount": float(invoice.amount),
            "currency": invoice.currency,
            "status": invoice.status,
            "invoice_date": invoice.invoice_date,
            "payment_method": invoice.payment_method
        }
        
        return create_success_response(
            message="Invoice created successfully",
            data=invoice_data
        )
    except Exception as e:
        return create_error_response(
            message="Failed to create invoice",
            errors=[ErrorDetail(field="invoice", message=f"Internal server error: {str(e)}")]
        )


@router.get("/usage-tracking", response_model=ApiResponse)
async def get_usage_tracking(
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Get usage tracking information"""
    try:
        usage_records = await subscription_service.get_usage_tracking(current_user.sub)
        usage_data = [
            {
                "usage_id": str(record.usage_id),
                "feature": record.feature,
                "used_count": record.used_count,
                "reset_cycle": record.reset_cycle,
                "last_reset": record.last_reset
            }
            for record in usage_records
        ]
        return create_success_response(
            message="Usage tracking retrieved successfully",
            data={"usage_records": usage_data}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve usage tracking",
            errors=[ErrorDetail(field="usage", message=f"Internal server error: {str(e)}")]
        )


# Admin endpoints
@router.post("/admin/cleanup-expired", response_model=ApiResponse)
async def cleanup_expired_subscriptions(
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Clean up expired subscriptions (admin endpoint)"""
    try:
        count = await subscription_service.cleanup_expired_subscriptions()
        return create_success_response(
            message=f"Cleaned up {count} expired subscriptions",
            data={"cleaned_count": count}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to cleanup expired subscriptions",
            errors=[ErrorDetail(field="admin", message=f"Internal server error: {str(e)}")]
        )


@router.get("/admin/usage-stats", response_model=ApiResponse)
async def get_usage_stats(
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get usage statistics (admin endpoint)"""
    try:
        # This would typically require admin authentication
        # For now, just return a placeholder
        return create_success_response(
            message="Usage statistics endpoint - requires admin authentication",
            data={"message": "This endpoint requires admin authentication"}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to get usage stats",
            errors=[ErrorDetail(field="admin", message=f"Internal server error: {str(e)}")]
        )
