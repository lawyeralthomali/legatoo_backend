from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from ..db.database import Base


class UsageTracking(Base):
    """Usage tracking model for monitoring feature usage"""
    __tablename__ = "usage_tracking"

    usage_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    subscription_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    feature = Column(String, nullable=False)  # file_upload, ai_chat, contract, token
    used_count = Column(Integer, nullable=False, default=0)
    reset_cycle = Column(String, nullable=False)  # daily / monthly / yearly
    last_reset = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscription = relationship("Subscription", back_populates="usage_tracking")

    def __repr__(self):
        return f"<UsageTracking(usage_id={self.usage_id}, subscription_id={self.subscription_id}, feature='{self.feature}', used_count={self.used_count})>"

    def should_reset(self) -> bool:
        """Check if usage should be reset based on cycle"""
        now = datetime.utcnow()
        
        if self.reset_cycle == 'daily':
            return (now - self.last_reset.replace(tzinfo=None)).days >= 1
        elif self.reset_cycle == 'monthly':
            return (now - self.last_reset.replace(tzinfo=None)).days >= 30
        elif self.reset_cycle == 'yearly':
            return (now - self.last_reset.replace(tzinfo=None)).days >= 365
        
        return False

    def reset_usage(self) -> None:
        """Reset usage count and update last_reset"""
        self.used_count = 0
        self.last_reset = datetime.utcnow()

    def increment_usage(self, amount: int = 1) -> int:
        """Increment usage count"""
        self.used_count += amount
        return self.used_count
