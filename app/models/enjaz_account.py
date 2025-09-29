"""
Enjaz Account model definition.

This module defines the SQLAlchemy model for Enjaz accounts,
allowing users to store encrypted Enjaz credentials.
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class EnjazAccount(Base, TimestampMixin):
    """Enjaz Account model representing encrypted Enjaz credentials."""
    
    __tablename__ = "enjaz_accounts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    username = Column(Text, nullable=False)  # Encrypted username
    password = Column(Text, nullable=False)  # Encrypted password
    
    # Relationships
    user = relationship("User", back_populates="enjaz_accounts")
    
    def __repr__(self):
        return f"<EnjazAccount(id={self.id}, user_id={self.user_id})>"
