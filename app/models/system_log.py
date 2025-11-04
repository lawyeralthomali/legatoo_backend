"""
System Log model for tracking system errors and logs.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from ..db.database import Base


class LogLevel(enum.Enum):
    """Log level enumeration."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SystemLog(Base):
    """System Log model for tracking errors and system events."""
    
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(SQLEnum(LogLevel), nullable=False, default=LogLevel.INFO, index=True)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True, index=True)
    method = Column(String(10), nullable=True)  # GET, POST, etc.
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Additional context
    correlation_id = Column(String(100), nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # If error is user-related
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level}, endpoint={self.endpoint}, created_at={self.created_at})>"
