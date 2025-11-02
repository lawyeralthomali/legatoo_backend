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
    active_only: bool = False,  # Changed to False to show all plans for admin
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
                "government_integration": getattr(plan, 'government_integration', None),
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


@router.post("/plans", response_model=ApiResponse)
async def create_plan(
    plan_data: dict,
    current_user: TokenData = Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service)
) -> ApiResponse:
    """Create a new subscription plan (admin only)"""
    try:
        # Validate required fields
        required_fields = ["plan_name", "plan_type", "price", "billing_cycle"]
        for field in required_fields:
            if field not in plan_data:
                return create_error_response(
                    message="Missing required field",
                    errors=[ErrorDetail(field=field, message=f"{field} is required")]
                )
        
        # Create plan
        plan = await plan_service.create_plan(plan_data)
        
        plan_response = {
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
            "government_integration": getattr(plan, 'government_integration', None),
            "description": plan.description,
            "is_active": plan.is_active
        }
        
        return create_success_response(
            message="Plan created successfully",
            data=plan_response
        )
    except Exception as e:
        return create_error_response(
            message="Failed to create plan",
            errors=[ErrorDetail(field="plan", message=f"Internal server error: {str(e)}")]
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


# Subscribers management endpoints
@router.get("/subscribers", response_model=ApiResponse)
async def get_all_subscribers(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Get all subscribers with their subscription and plan details"""
    try:
        subscriptions = await subscription_service.get_all_subscribers(skip=skip, limit=limit)
        subscribers_data = []
        
        for sub in subscriptions:
            subscriber_info = {
                "subscription_id": str(sub.subscription_id),
                "user_id": str(sub.user_id),
                "name": f"{sub.profile.first_name} {sub.profile.last_name}" if sub.profile else "Unknown",
                "email": sub.profile.email if sub.profile else None,
                "phone_number": sub.profile.phone_number if sub.profile else None,
                "plan_name": sub.plan.plan_name if sub.plan else None,
                "plan_type": sub.plan.plan_type if sub.plan else None,
                "price": float(sub.plan.price) if sub.plan else 0,
                "billing_cycle": sub.plan.billing_cycle if sub.plan else None,
                "start_date": sub.start_date.isoformat() if sub.start_date else None,
                "end_date": sub.end_date.isoformat() if sub.end_date else None,
                "status": sub.status.value if sub.status else None,
                "is_active": sub.is_active,
                "days_remaining": sub.days_remaining,
                "auto_renew": sub.auto_renew
            }
            subscribers_data.append(subscriber_info)
        
        return create_success_response(
            message="Subscribers retrieved successfully",
            data={"subscribers": subscribers_data, "count": len(subscribers_data)}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve subscribers",
            errors=[ErrorDetail(field="subscribers", message=f"Internal server error: {str(e)}")]
        )


@router.get("/subscribers/{subscription_id}", response_model=ApiResponse)
async def get_subscriber(
    subscription_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Get details of a specific subscriber"""
    try:
        subscription = await subscription_service.get_subscriber_by_id(subscription_id)
        
        if not subscription:
            return create_not_found_response(
                resource="Subscriber",
                field="subscription_id"
            )
        
        subscriber_data = {
            "subscription_id": str(subscription.subscription_id),
            "user_id": str(subscription.user_id),
            "name": f"{subscription.profile.first_name} {subscription.profile.last_name}" if subscription.profile else "Unknown",
            "email": subscription.profile.email if subscription.profile else None,
            "phone_number": subscription.profile.phone_number if subscription.profile else None,
            "account_type": subscription.profile.account_type if subscription.profile else None,
            "plan_id": str(subscription.plan_id),
            "plan_name": subscription.plan.plan_name if subscription.plan else None,
            "plan_type": subscription.plan.plan_type if subscription.plan else None,
            "price": float(subscription.plan.price) if subscription.plan else 0,
            "billing_cycle": subscription.plan.billing_cycle if subscription.plan else None,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
            "status": subscription.status.value if subscription.status else None,
            "is_active": subscription.is_active,
            "is_expired": subscription.is_expired,
            "is_cancelled": subscription.is_cancelled,
            "days_remaining": subscription.days_remaining,
            "auto_renew": subscription.auto_renew
        }
        
        return create_success_response(
            message="Subscriber details retrieved successfully",
            data=subscriber_data
        )
    except Exception as e:
        return create_error_response(
            message="Failed to retrieve subscriber details",
            errors=[ErrorDetail(field="subscriber", message=f"Internal server error: {str(e)}")]
        )


@router.post("/subscribers", response_model=ApiResponse)
async def create_subscriber(
    user_id: UUID,
    plan_id: UUID,
    duration_days: int = None,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Create a new subscription for a user (admin endpoint)"""
    try:
        subscription = await subscription_service.create_subscription_for_user(
            user_id=user_id,
            plan_id=plan_id,
            duration_days=duration_days
        )
        
        # Reload with relationships
        subscription = await subscription_service.get_subscriber_by_id(subscription.subscription_id)
        
        subscriber_data = {
            "subscription_id": str(subscription.subscription_id),
            "user_id": str(subscription.user_id),
            "name": f"{subscription.profile.first_name} {subscription.profile.last_name}" if subscription.profile else "Unknown",
            "email": subscription.profile.email if subscription.profile else None,
            "plan_name": subscription.plan.plan_name if subscription.plan else None,
            "plan_type": subscription.plan.plan_type if subscription.plan else None,
            "price": float(subscription.plan.price) if subscription.plan else 0,
            "billing_cycle": subscription.plan.billing_cycle if subscription.plan else None,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
            "status": subscription.status.value if subscription.status else None
        }
        
        return create_success_response(
            message="Subscriber created successfully",
            data=subscriber_data
        )
    except ValueError as e:
        return create_error_response(
            message="Failed to create subscriber",
            errors=[ErrorDetail(field="subscription", message=str(e))]
        )
    except Exception as e:
        return create_error_response(
            message="Failed to create subscriber",
            errors=[ErrorDetail(field="subscription", message=f"Internal server error: {str(e)}")]
        )


@router.put("/subscribers/{subscription_id}", response_model=ApiResponse)
async def update_subscriber(
    subscription_id: UUID,
    plan_id: UUID = None,
    status: str = None,
    end_date: str = None,
    auto_renew: bool = None,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Update subscriber subscription details"""
    try:
        from datetime import datetime
        
        end_date_dt = None
        if end_date:
            try:
                end_date_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return create_error_response(
                    message="Invalid end_date format",
                    errors=[ErrorDetail(field="end_date", message="end_date must be in ISO format")]
                )
        
        subscription = await subscription_service.update_subscription(
            subscription_id=subscription_id,
            plan_id=plan_id,
            status=status,
            end_date=end_date_dt,
            auto_renew=auto_renew
        )
        
        if not subscription:
            return create_not_found_response(
                resource="Subscription",
                field="subscription_id"
            )
        
        # Reload with relationships
        subscription = await subscription_service.get_subscriber_by_id(subscription_id)
        
        subscriber_data = {
            "subscription_id": str(subscription.subscription_id),
            "user_id": str(subscription.user_id),
            "name": f"{subscription.profile.first_name} {subscription.profile.last_name}" if subscription.profile else "Unknown",
            "email": subscription.profile.email if subscription.profile else None,
            "plan_name": subscription.plan.plan_name if subscription.plan else None,
            "plan_type": subscription.plan.plan_type if subscription.plan else None,
            "price": float(subscription.plan.price) if subscription.plan else 0,
            "billing_cycle": subscription.plan.billing_cycle if subscription.plan else None,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
            "status": subscription.status.value if subscription.status else None,
            "is_active": subscription.is_active,
            "days_remaining": subscription.days_remaining,
            "auto_renew": subscription.auto_renew
        }
        
        return create_success_response(
            message="Subscriber updated successfully",
            data=subscriber_data
        )
    except ValueError as e:
        return create_error_response(
            message="Failed to update subscriber",
            errors=[ErrorDetail(field="subscription", message=str(e))]
        )
    except Exception as e:
        return create_error_response(
            message="Failed to update subscriber",
            errors=[ErrorDetail(field="subscription", message=f"Internal server error: {str(e)}")]
        )


@router.delete("/subscribers/{subscription_id}", response_model=ApiResponse)
async def delete_subscriber(
    subscription_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
) -> ApiResponse:
    """Delete a subscriber subscription"""
    try:
        success = await subscription_service.delete_subscription(subscription_id)
        
        if not success:
            return create_not_found_response(
                resource="Subscription",
                field="subscription_id"
            )
        
        return create_success_response(
            message="Subscriber subscription deleted successfully",
            data={"deleted": True, "subscription_id": str(subscription_id)}
        )
    except Exception as e:
        return create_error_response(
            message="Failed to delete subscriber",
            errors=[ErrorDetail(field="subscription", message=f"Internal server error: {str(e)}")]
        )