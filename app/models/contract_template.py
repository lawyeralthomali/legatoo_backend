"""
Contract Template model definition.

This module defines SQLAlchemy models for contract templates and generated contracts.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, JSON, DateTime, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
import uuid

from ..db.database import Base


class ContractTemplate(Base):
    """Contract template model for storing reusable contract templates."""
    
    __tablename__ = "contract_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    file_path = Column(String(500), nullable=False)
    format = Column(String(10), CheckConstraint("format IN ('docx', 'html')"), default='docx', nullable=False)
    variables = Column(SQLiteJSON, nullable=False)  # JSON schema for form fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contracts = relationship("Contract", back_populates="template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ContractTemplate(id={self.id}, title='{self.title}')>"


class Contract(Base):
    """Generated contract model for storing user-created contracts."""
    
    __tablename__ = "contracts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String, ForeignKey("contract_templates.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filled_data = Column(SQLiteJSON, nullable=False)  # User-provided data
    pdf_path = Column(String(500), nullable=True)
    status = Column(String(50), default='generated', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    template = relationship("ContractTemplate", back_populates="contracts")
    
    def __repr__(self):
        return f"<Contract(id={self.id}, template_id={self.template_id}, owner_id={self.owner_id})>"

