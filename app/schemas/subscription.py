from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class StatusTypeEnum(str, Enum):
    """Subscription status enumeration for Pydantic"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SubscriptionBase(BaseModel):
    """Base subscription schema"""
    user_id: UUID
    plan_id: UUID
    start_date: datetime
    end_date: Optional[datetime] = None
    auto_renew: bool = Field(default=True)
    status: StatusTypeEnum = Field(default=StatusTypeEnum.ACTIVE)


class SubscriptionCreate(BaseModel):
    """Schema for creating a new subscription"""
    plan_id: UUID
    duration_days: Optional[int] = None


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription"""
    auto_renew: Optional[bool] = None
    status: Optional[StatusTypeEnum] = None


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response"""
    subscription_id: UUID
    is_active: bool
    is_expired: bool
    is_cancelled: bool
    days_remaining: int

    class Config:
        from_attributes = True


class SubscriptionStatusResponse(BaseModel):
    """Schema for subscription status response"""
    has_active_subscription: bool
    subscription: Optional[SubscriptionResponse] = None
    usage: Optional[Dict[str, Dict[str, int]]] = None


class FeatureUsageResponse(BaseModel):
    """Schema for feature usage response"""
    feature: str
    used: int
    limit: int
    remaining: int
    can_use: bool


class PlanResponse(BaseModel):
    """Schema for plan response"""
    plan_id: UUID
    plan_name: str
    plan_type: str
    price: float
    billing_cycle: str
    file_limit: Optional[int] = None
    ai_message_limit: Optional[int] = None
    contract_limit: Optional[int] = None
    report_limit: Optional[int] = None
    token_limit: Optional[int] = None
    multi_user_limit: Optional[int] = None
    government_integration: bool
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class BillingResponse(BaseModel):
    """Schema for billing response"""
    invoice_id: UUID
    amount: float
    currency: str
    status: str
    invoice_date: datetime
    payment_method: Optional[str] = None

    class Config:
        from_attributes = True


class UsageTrackingResponse(BaseModel):
    """Schema for usage tracking response"""
    usage_id: UUID
    feature: str
    used_count: int
    reset_cycle: str
    last_reset: Optional[datetime] = None

    class Config:
        from_attributes = True
