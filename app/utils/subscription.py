from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from uuid import UUID

from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
from ..services.subscription_service_new import SubscriptionServiceNew


async def verify_active_subscription(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI dependency that verifies if the user has an active subscription.
    
    Returns:
        Dict containing subscription status and plan information
        
    Raises:
        HTTPException: 403 if subscription is expired or inactive
    """
    try:
        user_id = current_user.sub
        
        # Get subscription status
        subscription_status = await SubscriptionServiceNew.get_subscription_status(db, user_id)
        
        # Check if user has an active subscription
        if not subscription_status['has_subscription']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active subscription found. Please subscribe to continue using premium features.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not subscription_status['is_active']:
            if subscription_status['is_expired']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your subscription has expired. Please renew to continue using premium features.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your subscription is inactive. Please contact support.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        
        return subscription_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying subscription: {str(e)}"
        )


async def verify_feature_access(
    feature: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI dependency that verifies if the user can access a specific feature.
    
    Args:
        feature: The feature to check access for (e.g., 'file_upload', 'ai_chat')
        
    Returns:
        Dict containing feature usage information
        
    Raises:
        HTTPException: 403 if user cannot access the feature
    """
    try:
        user_id = current_user.sub
        
        # Check if user can access the feature
        can_access = await SubscriptionServiceNew.check_feature_access(db, user_id, feature)
        
        if not can_access:
            # Get usage information for better error message
            usage_info = await SubscriptionServiceNew.get_feature_usage(db, user_id, feature)
            
            if usage_info['limit'] == 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{feature}' is not available in your current plan.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You have reached the limit for '{feature}'. Current usage: {usage_info['current_usage']}/{usage_info['limit']}",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        
        # Get detailed usage information
        usage_info = await SubscriptionServiceNew.get_feature_usage(db, user_id, feature)
        
        return usage_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking feature access: {str(e)}"
        )


async def get_subscription_status(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI dependency that returns subscription status without blocking access.
    
    Returns:
        Dict containing subscription status information
    """
    try:
        user_id = current_user.sub
        return await SubscriptionServiceNew.get_subscription_status(db, user_id)
        
    except Exception as e:
        # Return a default status if there's an error
        return {
            'has_subscription': False,
            'status': 'error',
            'plan': None,
            'features': {},
            'error': str(e)
        }


async def require_plan_type(
    plan_types: list,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI dependency that requires specific plan types.
    
    Args:
        plan_types: List of allowed plan types (e.g., ['monthly', 'annual'])
        
    Returns:
        Dict containing subscription status
        
    Raises:
        HTTPException: 403 if user doesn't have required plan type
    """
    try:
        user_id = current_user.sub
        
        # Get subscription status
        subscription_status = await SubscriptionServiceNew.get_subscription_status(db, user_id)
        
        if not subscription_status['has_subscription']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active subscription found. Please subscribe to continue.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        plan_type = subscription_status['plan']['plan_type']
        
        if plan_type not in plan_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires one of the following plan types: {', '.join(plan_types)}. Your current plan: {plan_type}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return subscription_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking plan type: {str(e)}"
        )


async def require_paid_plan(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI dependency that requires a paid plan (not free).
    
    Returns:
        Dict containing subscription status
        
    Raises:
        HTTPException: 403 if user has free plan
    """
    return await require_plan_type(['monthly', 'annual'], current_user, db)


async def require_enterprise_plan(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI dependency that requires enterprise-level features.
    
    Returns:
        Dict containing subscription status
        
    Raises:
        HTTPException: 403 if user doesn't have enterprise plan
    """
    try:
        user_id = current_user.sub
        
        # Get subscription status
        subscription_status = await SubscriptionServiceNew.get_subscription_status(db, user_id)
        
        if not subscription_status['has_subscription']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active subscription found. Please subscribe to continue.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        plan_name = subscription_status['plan']['plan_name'].lower()
        
        if 'enterprise' not in plan_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This feature requires an Enterprise plan. Please upgrade your subscription.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return subscription_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking enterprise plan: {str(e)}"
        )
