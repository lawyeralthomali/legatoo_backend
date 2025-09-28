"""
Role model and constants for user roles.

This module defines the role system with three levels:
- super_admin: Highest level, created only during database initialization
- admin: Default role for new signups
- user: Regular user role (for future use)
"""

from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..db.database import Base


class UserRole(str, Enum):
    """User role enumeration."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"


class Role(Base):
    """Role model for storing role information."""
    
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


# Role constants for easy access
ROLE_SUPER_ADMIN = UserRole.SUPER_ADMIN
ROLE_ADMIN = UserRole.ADMIN
ROLE_USER = UserRole.USER

# Default role for new signups
DEFAULT_USER_ROLE = ROLE_ADMIN

# Role hierarchy for permission checking
ROLE_HIERARCHY = {
    ROLE_SUPER_ADMIN: 3,
    ROLE_ADMIN: 2,
    ROLE_USER: 1
}

def get_role_level(role: UserRole) -> int:
    """Get the hierarchy level of a role."""
    return ROLE_HIERARCHY.get(role, 0)

def has_permission(user_role: UserRole, required_role: UserRole) -> bool:
    """Check if user role has permission based on hierarchy."""
    return get_role_level(user_role) >= get_role_level(required_role)
