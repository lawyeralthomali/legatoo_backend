from sqlalchemy import Column, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
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

    # Foreign key to Supabase auth.users.id (UUID)
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    
    # Profile information
    full_name = Column(Text, nullable=False)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    account_type = Column(Enum(AccountType), default=AccountType.PERSONAL) 
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<Profile(id={self.id}, full_name='{self.full_name}')>"
