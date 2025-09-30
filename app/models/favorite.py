from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base

class UserFavorite(Base):
    __tablename__ = "user_favorites"
    
    favorite_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    template_id = Column(Integer, ForeignKey('contract_templates.template_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # العلاقات
    user = relationship("User", back_populates="favorites")
    template = relationship("ContractTemplate", back_populates="favorites")
    
    def __repr__(self):
        return f"<UserFavorite(favorite_id={self.favorite_id}, user_id={self.user_id})>"