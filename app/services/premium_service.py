"""
Premium features service
Handles business logic for premium features and feature access
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from uuid import UUID
from fastapi import HTTPException, status

from ..services.subscription_service import SubscriptionService
from ..utils.subscription import (
    verify_active_subscription,
    verify_feature_access,
    get_subscription_status,
    require_paid_plan,
    require_enterprise_plan
)


class PremiumService:
    """Service for handling premium features business logic"""
    
    @staticmethod
    async def get_premium_status_data(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get premium status and feature information"""
        subscription_status = await get_subscription_status(
            {"sub": user_id}, db
        )
        
        return {
            "message": "Premium status information",
            "user_id": str(user_id),
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
    
    @staticmethod
    async def process_file_upload(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Process file upload with feature access validation"""
        # Check feature access
        feature_usage = await verify_feature_access("file_upload", {"sub": user_id}, db)
        
        # Increment usage
        await SubscriptionService.increment_feature_usage(
            db=db,
            user_id=user_id,
            feature="file_upload",
            amount=1
        )
        
        return {
            "message": "File uploaded successfully",
            "feature_usage": feature_usage,
            "file_id": "simulated_file_id_123"
        }
    
    @staticmethod
    async def process_ai_chat(
        db: AsyncSession, 
        user_id: UUID, 
        message: str = "Hello AI"
    ) -> Dict[str, Any]:
        """Process AI chat with feature access validation"""
        # Check feature access
        feature_usage = await verify_feature_access("ai_chat", {"sub": user_id}, db)
        
        # Increment usage
        await SubscriptionService.increment_feature_usage(
            db=db,
            user_id=user_id,
            feature="ai_chat",
            amount=1
        )
        
        return {
            "message": "AI chat used successfully",
            "user_message": message,
            "ai_response": "This is a simulated AI response",
            "feature_usage": feature_usage
        }
    
    @staticmethod
    async def process_contract_creation(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Process contract creation with feature access validation"""
        # Check feature access
        feature_usage = await verify_feature_access("contract", {"sub": user_id}, db)
        
        # Increment usage
        await SubscriptionService.increment_feature_usage(
            db=db,
            user_id=user_id,
            feature="contract",
            amount=1
        )
        
        return {
            "message": "Contract created successfully",
            "contract_id": "simulated_contract_123",
            "feature_usage": feature_usage
        }
    
    @staticmethod
    async def process_report_generation(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Process report generation with feature access validation"""
        # Check feature access
        feature_usage = await verify_feature_access("report", {"sub": user_id}, db)
        
        # Increment usage
        await SubscriptionService.increment_feature_usage(
            db=db,
            user_id=user_id,
            feature="report",
            amount=1
        )
        
        return {
            "message": "Report generated successfully",
            "report_id": "simulated_report_123",
            "feature_usage": feature_usage
        }
    
    @staticmethod
    async def process_token_usage(
        db: AsyncSession, 
        user_id: UUID, 
        amount: int = 100
    ) -> Dict[str, Any]:
        """Process token usage with feature access validation"""
        # Check feature access
        feature_usage = await verify_feature_access("token", {"sub": user_id}, db)
        
        # Increment usage
        await SubscriptionService.increment_feature_usage(
            db=db,
            user_id=user_id,
            feature="token",
            amount=amount
        )
        
        return {
            "message": f"Used {amount} tokens successfully",
            "feature_usage": feature_usage
        }
    
    @staticmethod
    async def process_user_management(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Process user management with feature access validation"""
        # Check feature access
        feature_usage = await verify_feature_access("multi_user", {"sub": user_id}, db)
        
        # Increment usage
        await SubscriptionService.increment_feature_usage(
            db=db,
            user_id=user_id,
            feature="multi_user",
            amount=1
        )
        
        return {
            "message": "User management accessed successfully",
            "feature_usage": feature_usage
        }
    
    @staticmethod
    async def get_paid_features_data(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get paid features data with plan validation"""
        subscription_status = await require_paid_plan({"sub": user_id}, db)
        
        return {
            "message": "Welcome to paid features!",
            "user_id": str(user_id),
            "plan_type": subscription_status['plan']['plan_type'],
            "features": [
                "Advanced AI chat",
                "Unlimited file uploads",
                "Priority support",
                "Advanced analytics"
            ]
        }
    
    @staticmethod
    async def get_enterprise_features_data(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get enterprise features data with plan validation"""
        subscription_status = await require_enterprise_plan({"sub": user_id}, db)
        
        return {
            "message": "Welcome to enterprise features!",
            "user_id": str(user_id),
            "plan_name": subscription_status['plan']['plan_name'],
            "features": [
                "Government integration",
                "Unlimited everything",
                "Dedicated support",
                "Custom integrations",
                "Advanced security"
            ]
        }
    
    @staticmethod
    async def get_government_integration_data(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get government integration data with enterprise plan validation"""
        subscription_status = await require_enterprise_plan({"sub": user_id}, db)
        
        # Check if plan has government integration
        if not subscription_status['plan'].get('government_integration', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Government integration is not available in your current plan"
            )
        
        return {
            "message": "Government integration accessed successfully",
            "user_id": str(user_id),
            "integration_status": "Connected",
            "available_services": [
                "Tax filing",
                "Business registration",
                "License renewal",
                "Compliance reporting"
            ]
        }
    
    @staticmethod
    async def get_feature_limits_data(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get feature limits data"""
        subscription_status = await get_subscription_status({"sub": user_id}, db)
        
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
    
    @staticmethod
    async def get_usage_summary_data(
        db: AsyncSession, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get usage summary data with percentage calculations"""
        subscription_status = await get_subscription_status({"sub": user_id}, db)
        
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
