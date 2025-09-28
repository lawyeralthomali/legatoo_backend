"""
Emergency Admin Routes

This module provides emergency endpoints for super admin management.
These endpoints should be used only in emergency situations when
the database is corrupted or the super admin needs to be recreated.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from ..db.database import get_db
from ..services.super_admin_service import SuperAdminService
from ..schemas.response import ApiResponse
from ..config.enhanced_logging import get_logger, log_security_event

# Create router
router = APIRouter(prefix="/api/v1/emergency", tags=["Emergency Admin"])

def get_correlation_id(request: Request) -> str:
    """Extract correlation ID from request headers or generate new one."""
    return request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

@router.post("/create-super-admin", response_model=ApiResponse)
async def create_super_admin_emergency(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Emergency endpoint to create super admin user.
    
    This endpoint should be used only in emergency situations when:
    - Database is corrupted
    - Super admin user is deleted
    - Initial database setup failed
    
    Returns:
        ApiResponse with creation status
    """
    correlation_id = get_correlation_id(request)
    logger = get_logger("emergency_admin", correlation_id)
    
    try:
        logger.warning("Emergency super admin creation requested")
        
        # Log security event
        log_security_event(
            "Emergency super admin creation requested",
            correlation_id=correlation_id,
            endpoint="/api/v1/emergency/create-super-admin"
        )
        
        # Create super admin service
        super_admin_service = SuperAdminService(correlation_id)
        
        # Create super admin
        result = await super_admin_service.create_super_admin(db)
        
        if result.success:
            logger.info("Emergency super admin creation successful")
            log_security_event(
                "Emergency super admin creation successful",
                correlation_id=correlation_id
            )
        else:
            logger.warning(f"Emergency super admin creation failed: {result.message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Emergency super admin creation error: {str(e)}")
        log_security_event(
            "Emergency super admin creation error",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to create emergency super admin",
                "data": None,
                "errors": [{"field": "super_admin", "message": str(e)}]
            }
        )

@router.post("/recreate-super-admin", response_model=ApiResponse)
async def recreate_super_admin_emergency(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Emergency endpoint to recreate super admin user.
    
    This will delete the existing super admin and create a new one.
    Use this only when the super admin account is compromised or corrupted.
    
    Returns:
        ApiResponse with recreation status
    """
    correlation_id = get_correlation_id(request)
    logger = get_logger("emergency_admin", correlation_id)
    
    try:
        logger.warning("Emergency super admin recreation requested")
        
        # Log security event
        log_security_event(
            "Emergency super admin recreation requested",
            correlation_id=correlation_id,
            endpoint="/api/v1/emergency/recreate-super-admin"
        )
        
        # Create super admin service
        super_admin_service = SuperAdminService(correlation_id)
        
        # Recreate super admin
        result = await super_admin_service.recreate_super_admin(db)
        
        if result.success:
            logger.info("Emergency super admin recreation successful")
            log_security_event(
                "Emergency super admin recreation successful",
                correlation_id=correlation_id
            )
        else:
            logger.warning(f"Emergency super admin recreation failed: {result.message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Emergency super admin recreation error: {str(e)}")
        log_security_event(
            "Emergency super admin recreation error",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to recreate emergency super admin",
                "data": None,
                "errors": [{"field": "super_admin", "message": str(e)}]
            }
        )

@router.get("/super-admin-status", response_model=ApiResponse)
async def get_super_admin_status(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if super admin exists in the database.
    
    This endpoint helps verify if the super admin is properly set up.
    
    Returns:
        ApiResponse with super admin status
    """
    correlation_id = get_correlation_id(request)
    logger = get_logger("emergency_admin", correlation_id)
    
    try:
        # Create super admin service
        super_admin_service = SuperAdminService(correlation_id)
        
        # Check if super admin exists
        exists = await super_admin_service.verify_super_admin_exists(db)
        
        if exists:
            # Get super admin info
            admin_info = await super_admin_service.get_super_admin_info(db)
            return ApiResponse(
                success=True,
                message="Super admin exists",
                data={
                    "exists": True,
                    "admin_info": admin_info
                }
            )
        else:
            return ApiResponse(
                success=True,
                message="Super admin does not exist",
                data={
                    "exists": False,
                    "admin_info": None
                }
            )
            
    except Exception as e:
        logger.error(f"Error checking super admin status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to check super admin status",
                "data": None,
                "errors": [{"field": "status", "message": str(e)}]
            }
        )
