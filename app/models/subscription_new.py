from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from ..db.database import Base


class Subscription(Base):
    """Enhanced subscription model with plan references and usage tracking"""
    __tablename__ = "subscriptions"

    subscription_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    plan_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)  # تاريخ انتهاء الاشتراك
    auto_renew = Column(Boolean, default=True)
    status = Column(String, nullable=False, default='active')  # active, expired, cancelled
    current_usage = Column(JSONB, default={})  # تخزين الاستخدام الحالي بصيغة JSON

    # Relationships
    plan = relationship("Plan", back_populates="subscriptions")
    usage_tracking = relationship("UsageTracking", back_populates="subscription")
    billing = relationship("Billing", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(subscription_id={self.subscription_id}, user_id={self.user_id}, plan_id={self.plan_id}, status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        if self.status != 'active':
            return False
        if self.end_date and datetime.utcnow() >= self.end_date.replace(tzinfo=None):
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Check if subscription is expired"""
        if self.status == 'expired':
            return True
        if self.end_date and datetime.utcnow() >= self.end_date.replace(tzinfo=None):
            return True
        return False

    @property
    def is_cancelled(self) -> bool:
        """Check if subscription is cancelled"""
        return self.status == 'cancelled'

    @property
    def days_remaining(self) -> int:
        """Get number of days remaining in subscription"""
        if not self.end_date:
            return 999999  # Unlimited
        if self.is_expired:
            return 0
        delta = self.end_date.replace(tzinfo=None) - datetime.utcnow()
        return max(0, delta.days)

    def get_usage(self, feature: str) -> int:
        """Get current usage for a specific feature"""
        if not self.current_usage:
            return 0
        return self.current_usage.get(feature, 0)

    def set_usage(self, feature: str, count: int) -> None:
        """Set usage for a specific feature"""
        if not self.current_usage:
            self.current_usage = {}
        self.current_usage[feature] = count

    def increment_usage(self, feature: str, amount: int = 1) -> int:
        """Increment usage for a specific feature"""
        current = self.get_usage(feature)
        new_count = current + amount
        self.set_usage(feature, new_count)
        return new_count

    def can_use_feature(self, feature: str) -> bool:
        """Check if user can use a specific feature based on plan limits"""
        if not self.plan:
            return False
        
        limit = self.plan.get_limit(feature)
        if limit == 0:  # Unlimited
            return True
        
        current_usage = self.get_usage(feature)
        return current_usage < limit

    def get_remaining_usage(self, feature: str) -> int:
        """Get remaining usage for a specific feature"""
        if not self.plan:
            return 0
        
        limit = self.plan.get_limit(feature)
        if limit == 0:  # Unlimited
            return 999999
        
        current_usage = self.get_usage(feature)
        return max(0, limit - current_usage)

    def extend_subscription(self, days: int) -> None:
        """Extend subscription by specified days"""
        if self.end_date:
            self.end_date = self.end_date + timedelta(days=days)
        else:
            self.end_date = datetime.utcnow() + timedelta(days=days)

    def cancel_subscription(self) -> None:
        """Cancel the subscription"""
        self.status = 'cancelled'
        self.auto_renew = False

    def expire_subscription(self) -> None:
        """Mark subscription as expired"""
        self.status = 'expired'
        self.auto_renew = False

    @classmethod
    def create_subscription(cls, user_id: str, plan_id: str, duration_days: int = None) -> "Subscription":
        """Create a new subscription"""
        start_date = datetime.utcnow()
        end_date = None
        
        if duration_days:
            end_date = start_date + timedelta(days=duration_days)
        
        return cls(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            status='active',
            current_usage={}
        )
