from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class ContractCategory(Base):
    __tablename__ = "contract_categories"
    
    category_id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey('contract_categories.category_id'), nullable=True)
    
    name_ar = Column(String(150), nullable=False)
    name_en = Column(String(150), nullable=False)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    
    legal_field = Column(String(50))  # 'مدني', 'تجاري', 'عمل'
    business_scope = Column(String(50))  # 'فردي', 'شركة_ناشئة', 'مؤسسة'
    complexity_level = Column(String(20))  # 'بسيط', 'متوسط', 'معقد'
    contract_type = Column(String(50))  # 'توظيف', 'شراكة', 'بيع'
    
    tags = Column(JSON)  # ['عقد_عمل', 'توظيف', 'سعودي']
    icon = Column(String(100), nullable=True)
    color_code = Column(String(7), nullable=True)
    
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    template_count = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # العلاقات
    parent = relationship("ContractCategory", remote_side=[category_id], back_populates="children")
    children = relationship("ContractCategory", back_populates="parent")
    templates = relationship("ContractTemplate", back_populates="category")
    
    def __repr__(self):
        return f"<ContractCategory(category_id={self.category_id}, name_ar='{self.name_ar}')>"