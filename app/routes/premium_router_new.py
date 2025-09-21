from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
from ..utils.subscription_new import (
    verify_active_subscription,
    verify_feature_access,
    get_subscription_status,
    require_paid_plan,
    require_enterprise_plan
)
from ..services.subscription_service_new import SubscriptionServiceNew

router = APIRouter(prefix="/premium", tags=["premium"])


@router.get("/status")
async def get_premium_status(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get premium status and feature information"""
    # Get subscription status
    subscription_status = await get_subscription_status(current_user, db)
    
    return {
        "message": "Premium status information",
        "user_id": str(current_user.sub),
        "subscription_status": subscription_status,
        "available_features": [
            "file_upload",
            "ai_chat", 
            "contract",
            "report",
            "token",
            "multi_user"
        ]
    }


@router.get("/file-upload")
async def upload_file(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file (requires file_upload feature access)"""
    # Check feature access
    feature_usage = await verify_feature_access("file_upload", current_user, db)
    
    # Simulate file upload
    await SubscriptionServiceNew.increment_feature_usage(
        db=db,
        user_id=current_user.sub,
        feature="file_upload",
        amount=1
    )
    
    return {
        "message": "File uploaded successfully",
        "feature_usage": feature_usage,
        "file_id": "simulated_file_id_123"
    }


@router.get("/ai-chat")
async def use_ai_chat(
    message: str = "Hello AI",
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Use AI chat (requires ai_chat feature access)"""
    # Check feature access
    feature_usage = await verify_feature_access("ai_chat", current_user, db)
    
    # Simulate AI chat
    await SubscriptionServiceNew.increment_feature_usage(
        db=db,
        user_id=current_user.sub,
        feature="ai_chat",
        amount=1
    )
    
    return {
        "message": "AI chat used successfully",
        "user_message": message,
        "ai_response": "This is a simulated AI response",
        "feature_usage": feature_usage
    }


@router.get("/contracts")
async def create_contract(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a contract (requires contract feature access)"""
    # Check feature access
    feature_usage = await verify_feature_access("contract", current_user, db)
    
    # Simulate contract creation
    await SubscriptionServiceNew.increment_feature_usage(
        db=db,
        user_id=current_user.sub,
        feature="contract",
        amount=1
    )
    
    return {
        "message": "Contract created successfully",
        "contract_id": "simulated_contract_123",
        "feature_usage": feature_usage
    }


@router.get("/reports")
async def generate_report(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a report (requires report feature access)"""
    # Check feature access
    feature_usage = await verify_feature_access("report", current_user, db)
    
    # Simulate report generation
    await SubscriptionServiceNew.increment_feature_usage(
        db=db,
        user_id=current_user.sub,
        feature="report",
        amount=1
    )
    
    return {
        "message": "Report generated successfully",
        "report_id": "simulated_report_123",
        "feature_usage": feature_usage
    }


@router.get("/tokens")
async def use_tokens(
    amount: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Use tokens (requires token feature access)"""
    # Check feature access
    feature_usage = await verify_feature_access("token", current_user, db)
    
    # Simulate token usage
    await SubscriptionServiceNew.increment_feature_usage(
        db=db,
        user_id=current_user.sub,
        feature="token",
        amount=amount
    )
    
    return {
        "message": f"Used {amount} tokens successfully",
        "feature_usage": feature_usage
    }


@router.get("/multi-user")
async def manage_users(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manage users (requires multi_user feature access)"""
    # Check feature access
    feature_usage = await verify_feature_access("multi_user", current_user, db)
    
    # Simulate user management
    await SubscriptionServiceNew.increment_feature_usage(
        db=db,
        user_id=current_user.sub,
        feature="multi_user",
        amount=1
    )
    
    return {
        "message": "User management accessed successfully",
        "feature_usage": feature_usage
    }


@router.get("/paid-features")
async def access_paid_features(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Access paid-only features (requires paid plan)"""
    # Check paid plan access
    subscription_status = await require_paid_plan(current_user, db)
    
    return {
        "message": "Welcome to paid features!",
        "user_id": str(current_user.sub),
        "plan_type": subscription_status['plan']['plan_type'],
        "features": [
            "Advanced AI chat",
            "Unlimited file uploads",
            "Priority support",
            "Advanced analytics"
        ]
    }


@router.get("/enterprise-features")
async def access_enterprise_features(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Access enterprise features (requires enterprise plan)"""
    # Check enterprise plan access
    subscription_status = await require_enterprise_plan(current_user, db)
    
    return {
        "message": "Welcome to enterprise features!",
        "user_id": str(current_user.sub),
        "plan_name": subscription_status['plan']['plan_name'],
        "features": [
            "Government integration",
            "Unlimited everything",
            "Dedicated support",
            "Custom integrations",
            "Advanced security"
        ]
    }


@router.get("/government-integration")
async def government_integration(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Access government integration (requires enterprise plan)"""
    # Check enterprise plan access
    subscription_status = await require_enterprise_plan(current_user, db)
    
    # Check if plan has government integration
    if not subscription_status['plan'].get('government_integration', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Government integration is not available in your current plan"
        )
    
    return {
        "message": "Government integration accessed successfully",
        "user_id": str(current_user.sub),
        "integration_status": "Connected",
        "available_services": [
            "Tax filing",
            "Business registration",
            "License renewal",
            "Compliance reporting"
        ]
    }


@router.get("/feature-limits")
async def get_feature_limits(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all feature limits for current user"""
    # Get subscription status
    subscription_status = await get_subscription_status(current_user, db)
    
    if not subscription_status['has_subscription']:
        return {
            "message": "No active subscription",
            "features": {}
        }
    
    return {
        "message": "Feature limits retrieved successfully",
        "plan_name": subscription_status['plan']['plan_name'],
        "features": subscription_status['features']
    }


@router.get("/usage-summary")
async def get_usage_summary(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage summary for current user"""
    # Get subscription status
    subscription_status = await get_subscription_status(current_user, db)
    
    if not subscription_status['has_subscription']:
        return {
            "message": "No active subscription",
            "usage": {}
        }
    
    # Calculate usage percentage for each feature
    usage_summary = {}
    for feature, info in subscription_status['features'].items():
        if info['limit'] > 0:
            percentage = (info['current_usage'] / info['limit']) * 100
        else:
            percentage = 0
        
        usage_summary[feature] = {
            **info,
            'usage_percentage': round(percentage, 2)
        }
    
    return {
        "message": "Usage summary retrieved successfully",
        "plan_name": subscription_status['plan']['plan_name'],
        "usage": usage_summary
    }
