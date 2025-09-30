"""
Base repository interfaces following the Repository pattern.

This module defines abstract base classes for repositories, ensuring
consistent data access patterns and enabling easy testing through mocking.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase


class IBaseRepository(ABC):
    """Base repository interface with common CRUD operations."""
    
    @abstractmethod
    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[Any]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get all entities with pagination."""
        pass
    
    @abstractmethod
    async def create(self, db: AsyncSession, entity_data: Dict[str, Any]) -> Any:
        """Create new entity."""
        pass
    
    @abstractmethod
    async def update(self, db: AsyncSession, id: int, entity_data: Dict[str, Any]) -> Optional[Any]:
        """Update entity by ID."""
        pass
    
    @abstractmethod
    async def delete(self, db: AsyncSession, id: int) -> bool:
        """Delete entity by ID."""
        pass


class IUserRepository(ABC):
    """Repository interface for user-related operations."""
    
    @abstractmethod
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Any]:
        """Get user by email address."""
        pass
    
    @abstractmethod
    async def email_exists(self, db: AsyncSession, email: str) -> bool:
        """Check if email already exists."""
        pass
    
    @abstractmethod
    async def create_user(self, db: AsyncSession, user_data: Dict[str, Any]) -> Any:
        """Create new user."""
        pass


class IProfileRepository(ABC):
    """Repository interface for profile-related operations."""
    
    @abstractmethod
    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[Any]:
        """Get profile by user ID."""
        pass
    
    @abstractmethod
    async def email_exists(self, db: AsyncSession, email: str) -> bool:
        """Check if email already exists in profiles."""
        pass
    
    @abstractmethod
    async def create_profile(self, db: AsyncSession, user_id: int, profile_data: Dict[str, Any]) -> Any:
        """Create new profile."""
        pass
    
    @abstractmethod
    async def update_profile(self, db: AsyncSession, user_id: int, profile_data: Dict[str, Any]) -> Optional[Any]:
        """Update profile by user ID."""
        pass
    
    @abstractmethod
    async def delete_profile(self, db: AsyncSession, user_id: int) -> bool:
        """Delete profile by user ID."""
        pass


class BaseRepository:
    """Base repository implementation with common functionality."""
    
    def __init__(self, db: AsyncSession, model: DeclarativeBase):
        """
        Initialize base repository.
        
        Args:
            db: Database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    async def get_by_id(self, id: int) -> Optional[Any]:
        """Get entity by ID."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get all entities with pagination."""
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, entity_data: Dict[str, Any]) -> Any:
        """Create new entity."""
        entity = self.model(**entity_data)
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def update(self, id: int, entity_data: Dict[str, Any]) -> Optional[Any]:
        """Update entity by ID."""
        result = await self.db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**entity_data)
            .returning(self.model)
        )
        entity = result.scalar_one_or_none()
        if entity:
            await self.db.commit()
        return entity
    
    async def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        if result.rowcount > 0:
            await self.db.commit()
            return True
        return False