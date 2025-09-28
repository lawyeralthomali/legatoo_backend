from sqlalchemy import Column, String, Numeric, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base


class Plan(Base):
    """Plan model for different subscription plans"""
    __tablename__ = "plans"

    plan_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    plan_name = Column(Text, nullable=False)  # Free Trial, Monthly, Annual
    plan_type = Column(Text, nullable=False)  # free, monthly, annual
    price = Column(Numeric(10, 2), nullable=False, default=0)  # السعر (0 للـ Free)
    billing_cycle = Column(Text, nullable=False)  # monthly / yearly / none
    file_limit = Column(Integer, nullable=True)  # عدد الملفات المسموح
    ai_message_limit = Column(Integer, nullable=True)  # عدد الرسائل
    contract_limit = Column(Integer, nullable=True)  # عدد العقود
    report_limit = Column(Integer, nullable=True)  # عدد التقارير القابلة للتصدير
    token_limit = Column(Integer, nullable=True)  # حد التوكنات
    multi_user_limit = Column(Integer, nullable=True)  # عدد المستخدمين المسموح
    government_integration = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self):
        return f"<Plan(plan_id={self.plan_id}, plan_name='{self.plan_name}', plan_type='{self.plan_type}')>"

    @property
    def is_free(self) -> bool:
        """Check if this is a free plan"""
        return self.plan_type == "free" or self.price == 0

    @property
    def is_paid(self) -> bool:
        """Check if this is a paid plan"""
        return not self.is_free

    def get_limit(self, feature: str) -> int:
        """Get the limit for a specific feature"""
        limits = {
            'file_upload': self.file_limit,
            'ai_chat': self.ai_message_limit,
            'contract': self.contract_limit,
            'report': self.report_limit,
            'token': self.token_limit,
            'multi_user': self.multi_user_limit
        }
        return limits.get(feature, 0) or 0
