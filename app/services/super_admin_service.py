"""
Super Admin Service

This service handles the creation and management of super admin users.
Super admin users are created only during database initialization or
in emergency situations when the database is corrupted.
"""

import os
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from ..models.user import User
from ..models.role import UserRole
from ..schemas.response import ApiResponse, raise_error_response
from ..config.enhanced_logging import get_logger, log_security_event

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SuperAdminService:
    """Service for managing super admin users."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id
        self.logger = get_logger("super_admin", correlation_id)
        
        # Super admin credentials from environment
        self.super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "info@legatoo.westlinktowing.com")
        self.super_admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "Zaq1zaq1zaq@@")
    
    async def create_super_admin(self, db: AsyncSession) -> ApiResponse:
        """
        Create the super admin user if it doesn't exist.
        
        Args:
            db: Database session
            
        Returns:
            ApiResponse with success/error information
        """
        try:
            # Check if super admin already exists
            existing_admin = await self._get_super_admin(db)
            if existing_admin:
                self.logger.info(f"Super admin already exists: {self.super_admin_email}")
                return ApiResponse(
                    success=True,
                    message="Super admin already exists",
                    data={
                        "email": self.super_admin_email,
                        "role": UserRole.SUPER_ADMIN,
                        "created_at": existing_admin.created_at.isoformat() if existing_admin.created_at else None
                    }
                )
            
            # Hash the password
            password_hash = pwd_context.hash(self.super_admin_password)
            
            # Create super admin user
            super_admin = User(
                email=self.super_admin_email,
                password_hash=password_hash,
                is_active=True,
                is_verified=True,  # Super admin is auto-verified
                role=UserRole.SUPER_ADMIN,
                email_sent=True,  # Mark as sent since it's auto-created
                email_sent_at=datetime.utcnow()
            )
            
            db.add(super_admin)
            await db.commit()
            await db.refresh(super_admin)
            
            # Log security event
            log_security_event(
                "Super admin user created",
                user_id=super_admin.id,
                email=self.super_admin_email,
                correlation_id=self.correlation_id
            )
            
            self.logger.info(f"Super admin created successfully: {self.super_admin_email}")
            
            return ApiResponse(
                success=True,
                message="Super admin created successfully",
                data={
                    "email": self.super_admin_email,
                    "role": UserRole.SUPER_ADMIN,
                    "created_at": super_admin.created_at.isoformat(),
                    "is_verified": True
                }
            )
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to create super admin: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Failed to create super admin user",
                field="super_admin"
            )
    
    async def recreate_super_admin(self, db: AsyncSession) -> ApiResponse:
        """
        Recreate the super admin user (for emergency situations).
        This will delete the existing super admin and create a new one.
        
        Args:
            db: Database session
            
        Returns:
            ApiResponse with success/error information
        """
        try:
            # Delete existing super admin if exists
            existing_admin = await self._get_super_admin(db)
            if existing_admin:
                await db.delete(existing_admin)
                await db.commit()
                self.logger.warning(f"Existing super admin deleted: {self.super_admin_email}")
            
            # Create new super admin
            return await self.create_super_admin(db)
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Failed to recreate super admin: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Failed to recreate super admin user",
                field="super_admin"
            )
    
    async def _get_super_admin(self, db: AsyncSession) -> Optional[User]:
        """Get the super admin user if it exists."""
        try:
            result = await db.execute(
                select(User).where(
                    User.email == self.super_admin_email,
                    User.role == UserRole.SUPER_ADMIN
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Error getting super admin: {str(e)}")
            return None
    
    async def verify_super_admin_exists(self, db: AsyncSession) -> bool:
        """
        Check if super admin exists in the database.
        
        Args:
            db: Database session
            
        Returns:
            True if super admin exists, False otherwise
        """
        try:
            super_admin = await self._get_super_admin(db)
            return super_admin is not None
        except Exception as e:
            self.logger.error(f"Error verifying super admin existence: {str(e)}")
            return False
    
    async def get_super_admin_info(self, db: AsyncSession) -> Optional[dict]:
        """
        Get super admin information without sensitive data.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with super admin info or None if not found
        """
        try:
            super_admin = await self._get_super_admin(db)
            if not super_admin:
                return None
            
            return {
                "id": super_admin.id,
                "email": super_admin.email,
                "role": super_admin.role,
                "is_active": super_admin.is_active,
                "is_verified": super_admin.is_verified,
                "created_at": super_admin.created_at.isoformat() if super_admin.created_at else None,
                "last_login": super_admin.last_login.isoformat() if super_admin.last_login else None
            }
        except Exception as e:
            self.logger.error(f"Error getting super admin info: {str(e)}")
            return None
