from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .category import ContractStructureBase, CategoryResponse

class TemplateBase(BaseModel):
    category_id: int
    title_ar: str
    title_en: str
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    contract_structure: ContractStructureBase
    variables_schema: Optional[dict] = None
    base_language: str = "ar"
    is_featured: bool = False
    is_premium: bool = False
    requires_legal_review: bool = False

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    title_ar: Optional[str] = None
    title_en: Optional[str] = None
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    contract_structure: Optional[ContractStructureBase] = None
    variables_schema: Optional[dict] = None
    is_featured: Optional[bool] = None
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None

class TemplateResponse(TemplateBase):
    template_id: int
    version: str
    is_active: bool = True
    usage_count: int = 0
    avg_rating: int = 0
    review_count: int = 0
    created_by: int
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None
    
    class Config:
        from_attributes = True