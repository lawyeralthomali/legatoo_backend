"""
Enhanced Contracts Library Models

Comprehensive models for contract management including AI generation,
versioning, revisions, and metadata tracking.
"""

from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
import uuid
import enum

from ..db.database import Base


class ContractStatus(enum.Enum):
    """Contract status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ContractLibrary(Base):
    """
    Enhanced contract model for the Contracts Library.
    Supports full CRUD, versioning, AI generation, and metadata.
    """
    
    __tablename__ = "contracts_library"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)  # Employment, NDA, Partnership, etc.
    jurisdiction = Column(String(100), nullable=True, index=True)  # country/region
    language = Column(String(10), default="en", nullable=False)
    status = Column(String(20), default=ContractStatus.DRAFT.value, nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    ai_generated = Column(Boolean, default=False, nullable=False)
    
    # Content
    content = Column(Text, nullable=True)  # Contract body/content
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    revisions = relationship("ContractRevision", back_populates="contract", cascade="all, delete-orphan", order_by="desc(ContractRevision.revision_number)")
    ai_requests = relationship("ContractAIRequest", back_populates="contract", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ContractLibrary(id={self.id}, title='{self.title}', status='{self.status}')>"


class ContractTemplateLibrary(Base):
    """
    Enhanced template model for reusable contract templates.
    Supports tags, placeholders, and public/private sharing.
    """
    
    __tablename__ = "contract_templates_library"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(300), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tags = Column(SQLiteJSON, nullable=True)  # List of tags: ["employment", "nda", "saudi-arabia"]
    content = Column(Text, nullable=False)  # Template body with placeholders like {{party_name}}, {{start_date}}
    language = Column(String(10), default="en", nullable=False)
    jurisdiction = Column(String(100), nullable=True, index=True)
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ContractTemplateLibrary(id={self.id}, name='{self.name}', is_public={self.is_public})>"


class ContractRevision(Base):
    """
    Revision history for contracts.
    Tracks changes, versions, and update metadata.
    """
    
    __tablename__ = "contract_revisions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = Column(String, ForeignKey("contracts_library.id"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    changes_summary = Column(Text, nullable=True)  # Human-readable summary of changes
    updated_content = Column(Text, nullable=False)  # Full contract content at this revision
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    contract = relationship("ContractLibrary", back_populates="revisions")
    
    def __repr__(self):
        return f"<ContractRevision(id={self.id}, contract_id={self.contract_id}, revision={self.revision_number})>"


class ContractAIRequest(Base):
    """
    Track AI generation requests for contracts.
    Stores prompts, model used, and generated content.
    """
    
    __tablename__ = "contract_ai_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prompt_text = Column(Text, nullable=False)  # User's natural language input
    ai_model = Column(String(50), default="gemini-2.0-flash-exp", nullable=False)  # Model used
    generated_content = Column(Text, nullable=True)  # AI-generated contract content
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    used_in_contract_id = Column(String, ForeignKey("contracts_library.id"), nullable=True, index=True)  # Link to contract if used
    
    # Relationships
    contract = relationship("ContractLibrary", back_populates="ai_requests")
    
    def __repr__(self):
        return f"<ContractAIRequest(id={self.id}, user_id={self.user_id}, model='{self.ai_model}')>"
