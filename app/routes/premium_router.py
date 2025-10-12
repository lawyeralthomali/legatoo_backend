from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
# Subscription utilities are now handled by PremiumService
from ..services.subscription.premium_service import PremiumService

router = APIRouter(prefix="/premium", tags=["premium"])


@router.get("/status")
async def get_premium_status(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get premium status and feature information"""
    return await PremiumService.get_premium_status_data(db, current_user.sub)


@router.get("/file-upload")
async def upload_file(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file (requires file_upload feature access)"""
    return await PremiumService.process_file_upload(db, current_user.sub)


@router.get("/ai-chat")
async def use_ai_chat(
    message: str = "Hello AI",
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Use AI chat (requires ai_chat feature access)"""
    return await PremiumService.process_ai_chat(db, current_user.sub, message)


@router.get("/contracts")
async def create_contract(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a contract (requires contract feature access)"""
    return await PremiumService.process_contract_creation(db, current_user.sub)


@router.get("/reports")
async def generate_report(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a report (requires report feature access)"""
    return await PremiumService.process_report_generation(db, current_user.sub)


@router.get("/tokens")
async def use_tokens(
    amount: int = 100,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Use tokens (requires token feature access)"""
    return await PremiumService.process_token_usage(db, current_user.sub, amount)


@router.get("/multi-user")
async def manage_users(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manage users (requires multi_user feature access)"""
    return await PremiumService.process_user_management(db, current_user.sub)


@router.get("/paid-features")
async def access_paid_features(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Access paid-only features (requires paid plan)"""
    return await PremiumService.get_paid_features_data(db, current_user.sub)


@router.get("/enterprise-features")
async def access_enterprise_features(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Access enterprise features (requires enterprise plan)"""
    return await PremiumService.get_enterprise_features_data(db, current_user.sub)


@router.get("/government-integration")
async def government_integration(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Access government integration (requires enterprise plan)"""
    return await PremiumService.get_government_integration_data(db, current_user.sub)


@router.get("/feature-limits")
async def get_feature_limits(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all feature limits for current user"""
    return await PremiumService.get_feature_limits_data(db, current_user.sub)


@router.get("/usage-summary")
async def get_usage_summary(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage summary for current user"""
    return await PremiumService.get_usage_summary_data(db, current_user.sub)
