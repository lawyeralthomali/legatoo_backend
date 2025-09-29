"""
Enjaz router for API endpoints.

This module provides REST API endpoints for Enjaz integration
including account management and case synchronization.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from ..db.database import get_db
from ..schemas.enjaz_schemas import EnjazCredentialsRequest
from ..schemas.response import ApiResponse
from ..services.enjaz_service import EnjazService
from ..utils.auth import get_current_user_id
from ..config.enhanced_logging import setup_logging, get_logger

router = APIRouter(prefix="/api/v1/enjaz", tags=["Enjaz Integration"])

# Setup logging
setup_logging()
logger = get_logger(__name__)


def get_enjaz_service(db: AsyncSession = Depends(get_db)) -> EnjazService:
    """Dependency provider for EnjazService."""
    return EnjazService(db)


@router.post("/connect", response_model=ApiResponse)
async def connect_enjaz(
    credentials: EnjazCredentialsRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    enjaz_service: EnjazService = Depends(get_enjaz_service)
) -> ApiResponse:
    """
    Connect Enjaz account with encrypted credentials.
    
    Args:
        credentials: Enjaz login credentials
        request: FastAPI request object
        user_id: Current authenticated user ID
        enjaz_service: Enjaz service (injected)
        
    Returns:
        ApiResponse: Response with connection status
        
    Raises:
        HTTPException: For validation errors or connection failures
    """
    try:
        logger.info(f"Enjaz connection request from user {user_id}")
        
        result = await enjaz_service.connect_enjaz_account(user_id, credentials)
        
        logger.info(f"Enjaz connection successful for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Enjaz connection failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sync-cases", response_model=ApiResponse)
async def sync_cases(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    enjaz_service: EnjazService = Depends(get_enjaz_service)
) -> ApiResponse:
    """
    Sync cases from Enjaz system for the authenticated user.
    
    Args:
        request: FastAPI request object
        user_id: Current authenticated user ID
        enjaz_service: Enjaz service (injected)
        
    Returns:
        ApiResponse: Response with sync results
        
    Raises:
        HTTPException: For sync failures or missing credentials
    """
    try:
        logger.info(f"Case sync request from user {user_id}")
        
        result = await enjaz_service.sync_cases(user_id)
        
        logger.info(f"Case sync completed for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Case sync failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cases", response_model=ApiResponse)
async def get_cases(
    request: Request,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of cases to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of cases to skip"),
    user_id: int = Depends(get_current_user_id),
    enjaz_service: EnjazService = Depends(get_enjaz_service)
) -> ApiResponse:
    """
    Get all cases for the authenticated user.
    
    Args:
        request: FastAPI request object
        limit: Maximum number of cases to return
        offset: Number of cases to skip
        user_id: Current authenticated user ID
        enjaz_service: Enjaz service (injected)
        
    Returns:
        ApiResponse: Response with cases list
        
    Raises:
        HTTPException: For retrieval failures
    """
    try:
        logger.info(f"Get cases request from user {user_id}, limit={limit}, offset={offset}")
        
        result = await enjaz_service.get_user_cases(user_id, limit, offset)
        
        logger.info(f"Retrieved {len(result.data.get('data', []))} cases for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Get cases failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/account-status", response_model=ApiResponse)
async def get_account_status(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    enjaz_service: EnjazService = Depends(get_enjaz_service)
) -> ApiResponse:
    """
    Get Enjaz account connection status for the authenticated user.
    
    Args:
        request: FastAPI request object
        user_id: Current authenticated user ID
        enjaz_service: Enjaz service (injected)
        
    Returns:
        ApiResponse: Response with account status
        
    Raises:
        HTTPException: For status check failures
    """
    try:
        logger.info(f"Account status request from user {user_id}")
        
        result = await enjaz_service.get_enjaz_account_status(user_id)
        
        logger.info(f"Account status retrieved for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Account status check failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/disconnect", response_model=ApiResponse)
async def disconnect_enjaz(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    enjaz_service: EnjazService = Depends(get_enjaz_service)
) -> ApiResponse:
    """
    Disconnect Enjaz account and delete all associated data.
    
    Args:
        request: FastAPI request object
        user_id: Current authenticated user ID
        enjaz_service: Enjaz service (injected)
        
    Returns:
        ApiResponse: Response confirming disconnection
        
    Raises:
        HTTPException: For disconnection failures
    """
    try:
        logger.info(f"Enjaz disconnection request from user {user_id}")
        
        result = await enjaz_service.disconnect_enjaz_account(user_id)
        
        logger.info(f"Enjaz disconnection completed for user {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Enjaz disconnection failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
