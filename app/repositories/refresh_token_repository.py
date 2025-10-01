"""
Refresh Token repository implementation.

This module provides data access operations for refresh tokens,
following the Repository pattern for clean separation of concerns.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from .base import BaseRepository
from ..models.refresh_token import RefreshToken


class RefreshTokenRepository(BaseRepository):
    """Repository for refresh token data access operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize refresh token repository.
        
        Args:
            db: Database session
        """
        super().__init__(db, RefreshToken)
    
    async def create_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        """
        Create a new refresh token.
        
        Args:
            user_id: User ID
            token_hash: Hashed token string
            expires_at: Token expiration datetime
            
        Returns:
            Created RefreshToken model
        """
        refresh_token = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            is_active=True
        )
        
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        
        return refresh_token
    
    async def get_valid_token(self, token_hash: str) -> Optional[RefreshToken]:
        """
        Get valid (active and not expired) refresh token by hash.
        
        Args:
            token_hash: Hashed token string
            
        Returns:
            RefreshToken if found and valid, None otherwise
        """
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.is_active == True,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            )
        )
        
        refresh_token = result.scalar_one_or_none()
        
        if refresh_token:
            # Update last used timestamp
            refresh_token.last_used_at = datetime.utcnow()
            await self.db.commit()
        
        return refresh_token
    
    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """
        Get refresh token by hash (regardless of status).
        
        Args:
            token_hash: Hashed token string
            
        Returns:
            RefreshToken if found, None otherwise
        """
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()
    
    async def revoke_token(self, token_hash: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            token_hash: Hashed token string
            
        Returns:
            True if token was revoked, False if not found
        """
        refresh_token = await self.get_by_token_hash(token_hash)
        
        if refresh_token:
            refresh_token.is_active = False
            await self.db.commit()
            return True
        
        return False
    
    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """
        Revoke all active refresh tokens for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of tokens revoked
        """
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_active == True
                )
            )
        )
        
        tokens = result.scalars().all()
        count = 0
        
        for token in tokens:
            token.is_active = False
            count += 1
        
        await self.db.commit()
        return count
    
    async def get_user_active_tokens(self, user_id: int) -> List[RefreshToken]:
        """
        Get all active refresh tokens for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active RefreshToken models
        """
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_active == True,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            ).order_by(RefreshToken.created_at.desc())
        )
        
        return result.scalars().all()
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired refresh tokens.
        
        Returns:
            Number of tokens cleaned up
        """
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.expires_at <= datetime.utcnow()
            )
        )
        
        tokens = result.scalars().all()
        count = 0
        
        for token in tokens:
            await self.db.delete(token)
            count += 1
        
        await self.db.commit()
        return count

