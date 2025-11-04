"""
User Session model for tracking active user sessions.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..db.database import Base


class UserSession(Base):
    """User Session model for tracking active sessions."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    location = Column(String(255), nullable=True)  # Country/City
    user_agent = Column(String(500), nullable=True)
    last_seen = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="sessions", lazy="select")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, last_seen={self.last_seen})>"
