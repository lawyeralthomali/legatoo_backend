from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class UserContract(Base):
    __tablename__ = "user_contracts"
    
    user_contract_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    template_id = Column(Integer, ForeignKey('contract_templates.template_id'))
    
    contract_data = Column(JSON)  # البيانات المدخلة من المستخدم
    final_content = Column(Text)  # المحتوى النهائي بعد التعبئة
    status = Column(String(50), default="draft")  # 'draft', 'completed', 'signed'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # العلاقات
    user = relationship("User", back_populates="user_contracts")
    template = relationship("ContractTemplate", back_populates="user_contracts")
    
    def __repr__(self):
        return f"<UserContract(user_contract_id={self.user_contract_id}, status='{self.status}')>"