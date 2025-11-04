"""
Analytics Router for admin dashboard analytics endpoints.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from ..db.database import get_db
from ..services.analytics_service import AnalyticsService
from ..schemas.response import ApiResponse, create_success_response
from ..utils.auth import get_current_user
from ..utils.role_auth import require_super_admin
from ..schemas.profile_schemas import TokenData
from ..models.login_history import LoginStatus
from ..models.system_log import LogLevel
from ..config.enhanced_logging import get_logger

router = APIRouter(prefix="/api/v1/admin/analytics", tags=["Admin Analytics"])


def get_analytics_service(correlation_id: Optional[str] = None) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(correlation_id)


@router.get("/online-users", response_model=ApiResponse)
async def get_online_users(
    request: Request,
    minutes_threshold: int = Query(1, ge=1, le=60, description="Minutes threshold for online status"),
    current_user: TokenData = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get count of currently online users."""
    correlation_id = request.headers.get("X-Correlation-ID", "no-correlation-id")
    service = get_analytics_service(correlation_id)
    
    try:
        count = await service.get_online_users_count(db, minutes_threshold)
        return create_success_response(
            message="Online users count retrieved",
            data={"online_users": count}
        )
    except Exception as e:
        logger = get_logger("analytics", correlation_id)
        logger.error(f"Error getting online users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get online users count")


@router.get("/online-users/over-time", response_model=ApiResponse)
async def get_online_users_over_time(
    request: Request,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    interval_minutes: int = Query(30, ge=5, le=120, description="Interval in minutes"),
    current_user: TokenData = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get online users count over time."""
    correlation_id = request.headers.get("X-Correlation-ID", "no-correlation-id")
    service = get_analytics_service(correlation_id)
    
    try:
        data = await service.get_online_users_over_time(db, hours, interval_minutes)
        return create_success_response(
            message="Online users over time retrieved",
            data={"chart_data": data}
        )
    except Exception as e:
        logger = get_logger("analytics", correlation_id)
        logger.error(f"Error getting online users over time: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get online users over time")


@router.get("/login-history", response_model=ApiResponse)
async def get_login_history(
    request: Request,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    status: Optional[str] = Query(None, description="Filter by status (success/failed)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get login history with filters."""
    correlation_id = request.headers.get("X-Correlation-ID", "no-correlation-id")
    service = get_analytics_service(correlation_id)
    
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
        # Parse status
        login_status = None
        if status:
            try:
                login_status = LoginStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        result = await service.get_login_history(
            db, user_id, start_dt, end_dt, login_status, limit, offset
        )
        
        return create_success_response(
            message="Login history retrieved",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger = get_logger("analytics", correlation_id)
        logger.error(f"Error getting login history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get login history")


@router.get("/system-logs", response_model=ApiResponse)
async def get_system_logs(
    request: Request,
    level: Optional[str] = Query(None, description="Filter by log level (info/warning/error/critical)"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get system logs with filters."""
    correlation_id = request.headers.get("X-Correlation-ID", "no-correlation-id")
    service = get_analytics_service(correlation_id)
    
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
        # Parse log level
        log_level = None
        if level:
            try:
                log_level = LogLevel(level.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid log level: {level}")
        
        result = await service.get_system_logs(
            db, log_level, endpoint, start_dt, end_dt, limit, offset
        )
        
        return create_success_response(
            message="System logs retrieved",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger = get_logger("analytics", correlation_id)
        logger.error(f"Error getting system logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system logs")


@router.get("/dashboard-stats", response_model=ApiResponse)
async def get_dashboard_stats(
    request: Request,
    current_user: TokenData = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse:
    """Get overall dashboard statistics."""
    correlation_id = request.headers.get("X-Correlation-ID", "no-correlation-id")
    service = get_analytics_service(correlation_id)
    
    try:
        stats = await service.get_dashboard_stats(db)
        
        # Also get chart data for online users over time (last 24 hours)
        chart_data = await service.get_online_users_over_time(db, hours=24, interval_minutes=30)
        stats["online_users_chart"] = chart_data
        
        return create_success_response(
            message="Dashboard stats retrieved",
            data=stats
        )
    except Exception as e:
        logger = get_logger("analytics", correlation_id)
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")
