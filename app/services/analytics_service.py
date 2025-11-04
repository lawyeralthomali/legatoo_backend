"""
Analytics Service for admin dashboard analytics.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from ..models.user_session import UserSession
from ..models.login_history import LoginHistory, LoginStatus
from ..models.system_log import SystemLog, LogLevel
from ..models.user import User
from ..models.profile import Profile
from ..config.enhanced_logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id
        self.logger = get_logger("analytics", correlation_id)
    
    async def get_online_users_count(self, db: AsyncSession, minutes_threshold: int = 1) -> int:
        """
        Get count of currently online users.
        
        A user is considered online if their last_seen is within the threshold.
        
        Args:
            db: Database session
            minutes_threshold: Minutes threshold for considering a user online (default: 1)
            
        Returns:
            Count of online users
        """
        try:
            threshold_time = datetime.utcnow() - timedelta(minutes=minutes_threshold)
            
            result = await db.execute(
                select(func.count(UserSession.id.distinct()))
                .join(User, UserSession.user_id == User.id)
                .where(
                    and_(
                        UserSession.last_seen >= threshold_time,
                        User.is_active == True
                    )
                )
            )
            
            count = result.scalar() or 0
            return count
            
        except Exception as e:
            self.logger.error(f"Error getting online users count: {str(e)}")
            return 0
    
    async def get_online_users_over_time(
        self, 
        db: AsyncSession, 
        hours: int = 24,
        interval_minutes: int = 30
    ) -> List[Dict]:
        """
        Get online users count over time.
        
        Args:
            db: Database session
            hours: Number of hours to look back
            interval_minutes: Interval in minutes for grouping
            
        Returns:
            List of dicts with timestamp and count
        """
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # For SQLite, we'll get all sessions and group them in Python
            # This is simpler and more portable
            result = await db.execute(
                select(UserSession.last_seen, UserSession.user_id)
                .where(UserSession.last_seen >= start_time)
                .order_by(UserSession.last_seen)
            )
            rows = result.all()
            
            # Group by time intervals
            intervals: Dict[str, set] = {}
            for row in rows:
                # Round down to nearest interval
                session_time = row.last_seen
                if isinstance(session_time, str):
                    session_time = datetime.fromisoformat(session_time.replace('Z', '+00:00'))
                
                # Round down to nearest interval_minutes
                minutes = session_time.minute
                rounded_minutes = (minutes // interval_minutes) * interval_minutes
                rounded_time = session_time.replace(minute=rounded_minutes, second=0, microsecond=0)
                time_key = rounded_time.strftime('%Y-%m-%d %H:%M')
                
                if time_key not in intervals:
                    intervals[time_key] = set()
                intervals[time_key].add(row.user_id)
            
            # Convert to list of dicts
            data = [
                {
                    "timestamp": time_key,
                    "count": len(user_ids)
                }
                for time_key, user_ids in sorted(intervals.items())
            ]
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting online users over time: {str(e)}")
            return []
    
    async def get_login_history(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[LoginStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        Get login history with filters.
        
        Args:
            db: Database session
            user_id: Filter by user ID (optional)
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            status: Filter by login status (optional)
            limit: Maximum number of records
            offset: Offset for pagination
            
        Returns:
            Dict with total count and records
        """
        try:
            query = select(LoginHistory)
            
            conditions = []
            if user_id:
                conditions.append(LoginHistory.user_id == user_id)
            if start_date:
                conditions.append(LoginHistory.login_time >= start_date)
            if end_date:
                conditions.append(LoginHistory.login_time <= end_date)
            if status:
                conditions.append(LoginHistory.status == status)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count(LoginHistory.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Get paginated results
            query = query.options(
                selectinload(LoginHistory.user).selectinload(User.profile)
            ).order_by(LoginHistory.login_time.desc()).limit(limit).offset(offset)
            
            result = await db.execute(query)
            records = result.scalars().all()
            
            return {
                "total": total,
                "records": [
                    {
                        "id": record.id,
                        "user_id": record.user_id,
                        "user_email": record.user.email if record.user else None,
                        "user_name": (
                            f"{record.user.profile.first_name} {record.user.profile.last_name}"
                            if record.user and record.user.profile
                            else None
                        ),
                        "login_time": record.login_time.isoformat() if record.login_time else None,
                        "ip_address": record.ip_address,
                        "location": record.location,
                        "device": record.device,
                        "status": record.status.value if record.status else None,
                        "failure_reason": record.failure_reason,
                    }
                    for record in records
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting login history: {str(e)}")
            return {"total": 0, "records": []}
    
    async def get_system_logs(
        self,
        db: AsyncSession,
        level: Optional[LogLevel] = None,
        endpoint: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        Get system logs with filters.
        
        Args:
            db: Database session
            level: Filter by log level (optional)
            endpoint: Filter by endpoint (optional)
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            limit: Maximum number of records
            offset: Offset for pagination
            
        Returns:
            Dict with total count and records
        """
        try:
            query = select(SystemLog)
            
            conditions = []
            if level:
                conditions.append(SystemLog.level == level)
            if endpoint:
                conditions.append(SystemLog.endpoint == endpoint)
            if start_date:
                conditions.append(SystemLog.created_at >= start_date)
            if end_date:
                conditions.append(SystemLog.created_at <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count(SystemLog.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Get paginated results
            query = query.order_by(SystemLog.created_at.desc()).limit(limit).offset(offset)
            
            result = await db.execute(query)
            records = result.scalars().all()
            
            return {
                "total": total,
                "records": [
                    {
                        "id": record.id,
                        "level": record.level.value if record.level else None,
                        "message": record.message,
                        "stack_trace": record.stack_trace,
                        "endpoint": record.endpoint,
                        "method": record.method,
                        "created_at": record.created_at.isoformat() if record.created_at else None,
                        "correlation_id": record.correlation_id,
                        "user_id": record.user_id,
                    }
                    for record in records
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system logs: {str(e)}")
            return {"total": 0, "records": []}
    
    async def get_dashboard_stats(self, db: AsyncSession) -> Dict:
        """
        Get overall dashboard statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dict with various statistics
        """
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)
            
            # Online users
            online_users = await self.get_online_users_count(db)
            
            # Total users
            total_users_result = await db.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            total_users = total_users_result.scalar() or 0
            
            # Errors today
            errors_today_result = await db.execute(
                select(func.count(SystemLog.id)).where(
                    and_(
                        SystemLog.level.in_([LogLevel.ERROR, LogLevel.CRITICAL]),
                        SystemLog.created_at >= today_start
                    )
                )
            )
            errors_today = errors_today_result.scalar() or 0
            
            # Active sessions (last 24 hours)
            active_sessions_result = await db.execute(
                select(func.count(func.distinct(UserSession.user_id))).where(
                    UserSession.last_seen >= yesterday_start
                )
            )
            active_sessions = active_sessions_result.scalar() or 0
            
            return {
                "online_users": online_users,
                "total_users": total_users,
                "errors_today": errors_today,
                "active_sessions": active_sessions,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard stats: {str(e)}")
            return {
                "online_users": 0,
                "total_users": 0,
                "errors_today": 0,
                "active_sessions": 0,
            }
