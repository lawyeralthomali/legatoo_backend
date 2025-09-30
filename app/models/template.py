from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class ContractTemplate(Base):
    __tablename__ = "contract_templates"
    
    template_id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('contract_categories.category_id'))
    
    version = Column(String(20), default="1.0")
    title_ar = Column(String(200), nullable=False)
    title_en = Column(String(200), nullable=False)
    description_ar = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    
    # هيكل البلوكات
    contract_structure = Column(JSON, nullable=False)
    variables_schema = Column(JSON, nullable=True)
    
    base_language = Column(String(10), default="ar")
    is_featured = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    requires_legal_review = Column(Boolean, default=False)
    
    usage_count = Column(Integer, default=0)
    avg_rating = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # العلاقات
    category = relationship("ContractCategory", back_populates="templates")
    user_contracts = relationship("UserContract", back_populates="template")
    favorites = relationship("UserFavorite", back_populates="template")
    
    def __repr__(self):
        return f"<ContractTemplate(template_id={self.template_id}, title_ar='{self.title_ar}')>"