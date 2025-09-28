"""
Base model definition for SQLAlchemy.

This module defines the base class for all SQLAlchemy models,
providing common functionality and configuration.
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin class for timestamp fields."""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
