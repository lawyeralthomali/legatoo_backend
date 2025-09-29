"""
Case Imported model definition.

This module defines the SQLAlchemy model for imported cases
from the Enjaz system.
"""

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class CaseImported(Base, TimestampMixin):
    """Case Imported model representing cases scraped from Enjaz."""
    
    __tablename__ = "cases_imported"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    case_number = Column(String(255), nullable=False, index=True)
    case_type = Column(String(255), nullable=False)
    status = Column(String(100), nullable=False)
    case_data = Column(Text, nullable=True)  # JSON data for additional case information
    
    # Relationships
    user = relationship("User", back_populates="cases_imported")
    
    def __repr__(self):
        return f"<CaseImported(id={self.id}, case_number={self.case_number}, user_id={self.user_id})>"
