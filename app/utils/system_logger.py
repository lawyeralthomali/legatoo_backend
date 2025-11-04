"""
System Logger utility for logging system events to the database.

This module provides functions to log various types of system events
(info, warning, error, critical) to the system_logs table.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import traceback
from datetime import datetime

from ..models.system_log import SystemLog, LogLevel
from ..db.database import AsyncSessionLocal
from ..config.enhanced_logging import get_logger

logger = get_logger(__name__)


async def log_system_event(
    level: LogLevel,
    message: str,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    user_id: Optional[int] = None,
    correlation_id: Optional[str] = None,
    stack_trace: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> Optional[SystemLog]:
    """
    Log a system event to the database.
    
    Args:
        level: Log level (INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        endpoint: Endpoint where the event occurred (optional)
        method: HTTP method (optional)
        user_id: User ID if event is user-related (optional)
        correlation_id: Correlation ID for request tracking (optional)
        stack_trace: Stack trace for errors (optional)
        db: Database session (optional, will create new if not provided)
        
    Returns:
        SystemLog instance if successful, None otherwise
    """
    should_close = False
    if db is None:
        db = AsyncSessionLocal()
        should_close = True
    
    try:
        log_entry = SystemLog(
            level=level,
            message=message,
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            correlation_id=correlation_id,
            stack_trace=stack_trace,
            created_at=datetime.utcnow()
        )
        
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        
        return log_entry
        
    except Exception as e:
        await db.rollback()
        logger.warning(f"Failed to log system event to database: {str(e)}")
        return None
    finally:
        if should_close:
            await db.close()


async def log_info(
    message: str,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    user_id: Optional[int] = None,
    correlation_id: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> Optional[SystemLog]:
    """Log an info-level event."""
    return await log_system_event(
        level=LogLevel.INFO,
        message=message,
        endpoint=endpoint,
        method=method,
        user_id=user_id,
        correlation_id=correlation_id,
        db=db
    )


async def log_warning(
    message: str,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    user_id: Optional[int] = None,
    correlation_id: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> Optional[SystemLog]:
    """Log a warning-level event."""
    return await log_system_event(
        level=LogLevel.WARNING,
        message=message,
        endpoint=endpoint,
        method=method,
        user_id=user_id,
        correlation_id=correlation_id,
        db=db
    )


async def log_error(
    message: str,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    user_id: Optional[int] = None,
    correlation_id: Optional[str] = None,
    exception: Optional[Exception] = None,
    stack_trace: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> Optional[SystemLog]:
    """Log an error-level event with optional exception."""
    if exception and not stack_trace:
        try:
            stack_trace = traceback.format_exception(type(exception), exception, exception.__traceback__)
            stack_trace = "".join(stack_trace)
        except Exception:
            stack_trace = str(exception)
    
    return await log_system_event(
        level=LogLevel.ERROR,
        message=message,
        endpoint=endpoint,
        method=method,
        user_id=user_id,
        correlation_id=correlation_id,
        stack_trace=stack_trace,
        db=db
    )


async def log_critical(
    message: str,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    user_id: Optional[int] = None,
    correlation_id: Optional[str] = None,
    exception: Optional[Exception] = None,
    stack_trace: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> Optional[SystemLog]:
    """Log a critical-level event with optional exception."""
    if exception and not stack_trace:
        try:
            stack_trace = traceback.format_exception(type(exception), exception, exception.__traceback__)
            stack_trace = "".join(stack_trace)
        except Exception:
            stack_trace = str(exception)
    
    return await log_system_event(
        level=LogLevel.CRITICAL,
        message=message,
        endpoint=endpoint,
        method=method,
        user_id=user_id,
        correlation_id=correlation_id,
        stack_trace=stack_trace,
        db=db
    )
