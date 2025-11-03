"""
Support Ticket Model.

This module defines the database model for support tickets.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..db.database import Base


class TicketStatus(str, enum.Enum):
    """Support ticket status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    """Support ticket priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SupportTicket(Base):
    """
    Model for storing support tickets.
    
    Allows users to submit support requests with categories, priorities, and status tracking.
    """
    
    __tablename__ = "support_tickets"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User information
    user_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Ticket details
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)  # e.g., "technical", "billing", "general", "bug_report"
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN, nullable=False, index=True)
    
    # Response information
    admin_response = Column(Text, nullable=True)
    admin_id = Column(Integer, ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    
    # Attachments (stored as JSON array of file paths)
    attachments = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("Profile", foreign_keys=[user_id], lazy="select")
    admin = relationship("Profile", foreign_keys=[admin_id], lazy="select")
    
    def __repr__(self):
        return f"<SupportTicket(id={self.id}, subject='{self.subject[:30]}...', status='{self.status}', priority='{self.priority}')>"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "subject": self.subject,
            "description": self.description,
            "category": self.category,
            "priority": self.priority.value if isinstance(self.priority, TicketPriority) else self.priority,
            "status": self.status.value if isinstance(self.status, TicketStatus) else self.status,
            "admin_response": self.admin_response,
            "admin_id": self.admin_id,
            "attachments": self.attachments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

