"""
Login History model for tracking user login attempts.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from ..db.database import Base


class LoginStatus(enum.Enum):
    """Login status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"


class LoginHistory(Base):
    """Login History model for tracking login attempts."""
    
    __tablename__ = "login_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for failed attempts
    login_time = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    location = Column(String(255), nullable=True)  # Country/City
    device = Column(String(255), nullable=True)  # Browser/Device info
    user_agent = Column(String(500), nullable=True)
    status = Column(SQLEnum(LoginStatus), nullable=False, default=LoginStatus.SUCCESS, index=True)
    failure_reason = Column(String(255), nullable=True)  # Reason for failed login
    
    # Relationships
    user = relationship("User", backref="login_history", lazy="select")
    
    def __repr__(self):
        return f"<LoginHistory(id={self.id}, user_id={self.user_id}, status={self.status}, login_time={self.login_time})>"
