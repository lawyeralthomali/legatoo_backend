import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from ..db.database import Base

class StatusType(enum.Enum):
    """Subscription status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Subscription(Base):
    """Subscription model with plan references and usage tracking"""
    __tablename__ = "subscriptions"

    subscription_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("profiles.id"), nullable=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.plan_id"), nullable=True, index=True)
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    status = Column(Enum(StatusType), nullable=False, default=StatusType.ACTIVE)

    # Relationships
    plan = relationship("Plan", back_populates="subscriptions")
    profile = relationship("Profile", foreign_keys=[user_id])
    # Note: usage_records relationship removed due to missing foreign key constraints
    # Can be added back after running add_missing_foreign_keys.sql

    def __repr__(self):
        return f"<Subscription(subscription_id={self.subscription_id}, user_id={self.user_id}, plan_id={self.plan_id}, status='{self.status.value}')>"

    @property
    def is_active(self) -> bool:
        if self.status != StatusType.ACTIVE:
            return False
        if self.end_date and datetime.utcnow() >= self.end_date.replace(tzinfo=None):
            return False
        return True

    @property
    def is_expired(self) -> bool:
        if self.status == StatusType.EXPIRED:
            return True
        if self.end_date and datetime.utcnow() >= self.end_date.replace(tzinfo=None):
            return True
        return False

    @property
    def is_cancelled(self) -> bool:
        return self.status == StatusType.CANCELLED

    @property
    def days_remaining(self) -> int:
        if not self.end_date:
            return 999999  # Unlimited
        if self.is_expired:
            return 0
        delta = self.end_date.replace(tzinfo=None) - datetime.utcnow()
        return max(0, delta.days)

    def extend_subscription(self, days: int) -> None:
        if self.end_date:
            self.end_date = self.end_date + timedelta(days=days)
        else:
            self.end_date = datetime.utcnow() + timedelta(days=days)

    def cancel_subscription(self) -> None:
        self.status = StatusType.CANCELLED
        self.auto_renew = False

    def expire_subscription(self) -> None:
        self.status = StatusType.EXPIRED
        self.auto_renew = False

    @classmethod
    def create_subscription(cls, user_id: str, plan_id: str, duration_days: int = None) -> "Subscription":
        start_date = datetime.utcnow()
        end_date = None
        if duration_days:
            end_date = start_date + timedelta(days=duration_days)
        return cls(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            status=StatusType.ACTIVE
        )
