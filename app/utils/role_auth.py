"""
Role-based authentication utilities.

This module provides utilities for role-based access control,
including permission checking and role validation.
"""

from fastapi import HTTPException, status, Depends
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.database import get_db
from ..models.user import User
from ..models.role import UserRole, has_permission, get_role_level
from ..utils.auth import get_current_user
from ..schemas.profile_schemas import TokenData


class RoleChecker:
    """Role-based permission checker."""
    
    def __init__(self, required_role: UserRole):
        self.required_role = required_role
    
    def __call__(self, current_user: TokenData = Depends(get_current_user)) -> TokenData:
        """Check if current user has required role."""
        # For now, we'll use a simple role check
        # In a full implementation, you'd fetch the user from database
        # and check their actual role
        
        # This is a placeholder - in real implementation you'd:
        # 1. Get user from database using current_user.sub
        # 2. Check user.role against required_role
        # 3. Use has_permission(user.role, required_role)
        
        return current_user


def require_role(required_role: UserRole):
    """Create a dependency that requires a specific role."""
    return RoleChecker(required_role)


def require_super_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require super admin role."""
    # Placeholder - in real implementation, check user role from database
    return current_user


def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require admin or super admin role."""
    # Placeholder - in real implementation, check user role from database
    return current_user


def require_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Require any authenticated user."""
    return current_user


async def get_user_role_from_db(
    user_id: int,
    db: AsyncSession
) -> Optional[UserRole]:
    """
    Get user role from database.
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        UserRole: User's role or None if not found
    """
    try:
        result = await db.execute(
            select(User.role).where(User.id == user_id)
        )
        role_str = result.scalar_one_or_none()
        
        if role_str:
            return UserRole(role_str)
        return None
        
    except Exception:
        return None


async def check_user_permission(
    user_id: int,
    required_role: UserRole,
    db: AsyncSession
) -> bool:
    """
    Check if user has required permission.
    
    Args:
        user_id: User ID
        required_role: Required role
        db: Database session
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    user_role = await get_user_role_from_db(user_id, db)
    
    if not user_role:
        return False
    
    return has_permission(user_role, required_role)


def create_role_dependency(required_role: UserRole):
    """
    Create a FastAPI dependency for role-based access control.
    
    Args:
        required_role: Required role level
        
    Returns:
        Dependency function
    """
    async def role_dependency(
        current_user: TokenData = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> TokenData:
        """Check if current user has required role."""
        
        # Get user from database
        result = await db.execute(
            select(User).where(User.email == current_user.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check role permission
        if not has_permission(UserRole(user.role), required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        
        return current_user
    
    return role_dependency


# Pre-defined role dependencies
require_super_admin_role = create_role_dependency(UserRole.SUPER_ADMIN)
require_admin_role = create_role_dependency(UserRole.ADMIN)
require_user_role = create_role_dependency(UserRole.USER)


class RolePermissions:
    """Role permission definitions."""
    
    # Super Admin permissions
    SUPER_ADMIN_PERMISSIONS = [
        "user.create",
        "user.read",
        "user.update",
        "user.delete",
        "role.manage",
        "system.admin",
        "database.admin"
    ]
    
    # Admin permissions
    ADMIN_PERMISSIONS = [
        "user.create",
        "user.read",
        "user.update",
        "profile.manage",
        "subscription.manage"
    ]
    
    # User permissions
    USER_PERMISSIONS = [
        "profile.read",
        "profile.update",
        "subscription.read"
    ]
    
    @classmethod
    def get_permissions(cls, role: UserRole) -> List[str]:
        """Get permissions for a role."""
        if role == UserRole.SUPER_ADMIN:
            return cls.SUPER_ADMIN_PERMISSIONS
        elif role == UserRole.ADMIN:
            return cls.ADMIN_PERMISSIONS
        elif role == UserRole.USER:
            return cls.USER_PERMISSIONS
        else:
            return []
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: str) -> bool:
        """Check if role has specific permission."""
        permissions = cls.get_permissions(role)
        return permission in permissions
