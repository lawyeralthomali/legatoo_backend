"""
Case Analysis History Model.

This module defines the database model for storing legal case analysis history.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base


class CaseAnalysis(Base):
    """
    Model for storing legal case analysis history.
    
    Stores comprehensive AI-generated analysis results with all metadata
    to allow users to view and download their analysis history.
    """
    
    __tablename__ = "case_analyses"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User and file information
    user_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    file_size_mb = Column(Float, nullable=True)
    
    # Analysis metadata
    analysis_type = Column(String(50), nullable=False, index=True)  # 'case-analysis' or 'contract-review'
    lawsuit_type = Column(String(100), nullable=False)
    result_seeking = Column(Text, nullable=True)
    user_context = Column(Text, nullable=True)
    
    # Analysis results - stored as JSON for flexibility
    analysis_data = Column(JSON, nullable=False)  # Full analysis data structure
    risk_score = Column(Integer, nullable=True)  # 0-100
    risk_label = Column(String(20), nullable=True)  # Low, Medium, High, Critical
    raw_response = Column(Text, nullable=True)  # Raw Gemini response
    
    # Additional files (if multiple files were uploaded)
    additional_files = Column(JSON, nullable=True)  # Array of additional file metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    profile = relationship("Profile", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<CaseAnalysis(id={self.id}, filename='{self.filename}', analysis_type='{self.analysis_type}', created_at='{self.created_at}')>"
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_size_mb": self.file_size_mb,
            "analysis_type": self.analysis_type,
            "lawsuit_type": self.lawsuit_type,
            "result_seeking": self.result_seeking,
            "user_context": self.user_context,
            "analysis_data": self.analysis_data,
            "risk_score": self.risk_score,
            "risk_label": self.risk_label,
            "additional_files": self.additional_files,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

