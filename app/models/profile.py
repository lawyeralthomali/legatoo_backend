from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base
import enum


class AccountType(enum.Enum):
    """Account type enumeration"""
    PERSONAL = "personal"
    BUSINESS = "business"


# Create the PostgreSQL enum type
account_type_enum = ENUM('personal', 'business', name='account_type_enum', create_type=False)


class Profile(Base):
    __tablename__ = "profiles"

    # Foreign key to Supabase auth.users.id (UUID)
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    
    # Profile information
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    avatar_url = Column(Text, nullable=True)
    phone_number = Column(Text, nullable=True)
    account_type = Column(account_type_enum, default="personal") 
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<Profile(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}')>"
