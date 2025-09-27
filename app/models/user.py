"""
User model definition.

This module defines the SQLAlchemy model for users,
following the domain-driven design principles.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


from ..db.database import Base

class User(Base):
    """User model representing authenticated users."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships - using string reference to avoid circular imports
    profile = relationship("Profile", back_populates="user", uselist=False, lazy="select")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
