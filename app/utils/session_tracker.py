"""
Session tracking utilities for analytics.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import Optional

from ..models.user_session import UserSession
from ..models.login_history import LoginHistory, LoginStatus
from ..config.enhanced_logging import get_logger

logger = get_logger(__name__)


async def update_user_session(
    db: AsyncSession,
    user_id: int,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """
    Update or create user session record.
    
    Args:
        db: Database session
        user_id: User ID
        ip_address: User's IP address
        user_agent: User's user agent string
    """
    try:
        # Try to find existing session for this user
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.last_seen >= datetime.utcnow() - timedelta(minutes=30)
                )
            )
        )
        session = result.scalar_one_or_none()
        
        if session:
            # Update existing session
            session.last_seen = datetime.utcnow()
            if ip_address:
                session.ip_address = ip_address
            if user_agent:
                session.user_agent = user_agent
        else:
            # Create new session
            location = get_location_from_ip(ip_address) if ip_address else None
            
            session = UserSession(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location,
                last_seen=datetime.utcnow()
            )
            db.add(session)
        
        await db.commit()
        
    except Exception as e:
        logger.warning(f"Error updating user session: {str(e)}")
        await db.rollback()
        # Don't raise - session tracking is not critical


async def log_login_attempt(
    db: AsyncSession,
    user_id: Optional[int],
    ip_address: Optional[str],
    user_agent: Optional[str],
    status: LoginStatus,
    failure_reason: Optional[str] = None
) -> None:
    """
    Log a login attempt to the database.
    
    Args:
        db: Database session
        user_id: User ID (None for failed attempts with unknown user)
        ip_address: User's IP address
        user_agent: User's user agent string
        status: Login status (success or failed)
        failure_reason: Reason for failure (if failed)
    """
    try:
        location = get_location_from_ip(ip_address) if ip_address else None
        device = parse_user_agent(user_agent) if user_agent else None
        
        login_record = LoginHistory(
            user_id=user_id,
            login_time=datetime.utcnow(),
            ip_address=ip_address,
            location=location,
            device=device,
            user_agent=user_agent,
            status=status,
            failure_reason=failure_reason
        )
        
        db.add(login_record)
        await db.commit()
        
        # If successful login, also create/update session
        if status == LoginStatus.SUCCESS and user_id:
            await update_user_session(db, user_id, ip_address, user_agent)
            
    except Exception as e:
        logger.warning(f"Error logging login attempt: {str(e)}")
        await db.rollback()
        # Don't raise - login logging is not critical


def get_location_from_ip(ip_address: str) -> Optional[str]:
    """
    Get location string from IP address.
    
    Args:
        ip_address: IP address
        
    Returns:
        Location string (e.g., "US, New York") or None
    """
    try:
        # For now, return a simple format
        # In production, you'd use a GeoIP service like MaxMind GeoIP2
        # This is a placeholder implementation
        return None  # Could implement GeoIP lookup here
        
    except Exception:
        return None


def parse_user_agent(user_agent: str) -> Optional[str]:
    """
    Parse user agent string to extract device/browser info.
    
    Args:
        user_agent: User agent string
        
    Returns:
        Device string (e.g., "Chrome on Windows") or None
    """
    try:
        # Simple parsing - could use user_agents library for better parsing
        if "Chrome" in user_agent:
            return "Chrome"
        elif "Firefox" in user_agent:
            return "Firefox"
        elif "Safari" in user_agent:
            return "Safari"
        elif "Edge" in user_agent:
            return "Edge"
        else:
            return "Unknown"
            
    except Exception:
        return None
