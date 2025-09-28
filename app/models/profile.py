from sqlalchemy import Column, String, DateTime, Text, UniqueConstraint, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base
import enum


class AccountType(enum.Enum):
    """Account type enumeration"""
    PERSONAL = "personal"
    BUSINESS = "business"


class Profile(Base):
    __tablename__ = "profiles"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Profile information
    email = Column(Text, nullable=False)
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    avatar_url = Column(Text, nullable=True)
    phone_number = Column(Text, nullable=True, unique=True, index=True)
    account_type = Column(String(20), default="personal") 
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    
    # Relationships - using string references to avoid circular imports
    user = relationship("User", back_populates="profile", lazy="select")
    uploaded_documents = relationship("LegalDocument", back_populates="uploaded_by", lazy="select")
    
    # Table constraints (will be added after migration)
    # __table_args__ = (
    #     UniqueConstraint('user_id', name='uq_profiles_user_id'),
    # )

    def __repr__(self):
        return f"<Profile(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}')>"
