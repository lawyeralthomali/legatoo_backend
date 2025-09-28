"""
User model definition.

This module defines the SQLAlchemy model for users,
following the domain-driven design principles.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..db.database import Base
from .role import UserRole, DEFAULT_USER_ROLE

class User(Base):
    """User model representing authenticated users."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True, unique=True, index=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Security fields
    last_login = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Email verification status
    email_sent = Column(Boolean, default=False, nullable=False)
    email_sent_at = Column(DateTime, nullable=True)
    
    # Password reset fields
    password_reset_token = Column(String(255), nullable=True, unique=True, index=True)
    password_reset_token_expires = Column(DateTime, nullable=True)
    
    # Role field
    role = Column(String(20), default=DEFAULT_USER_ROLE, nullable=False, index=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships - using string reference to avoid circular imports
    profile = relationship("Profile", back_populates="user", uselist=False, lazy="select")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.role == UserRole.SUPER_ADMIN
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin or super admin."""
        return self.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    @property
    def is_user(self) -> bool:
        """Check if user is regular user."""
        return self.role == UserRole.USER
