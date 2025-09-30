from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ClauseFieldBase(BaseModel):
    name: str
    type: str  # 'text', 'number', 'date', 'select'
    label_ar: str
    label_en: str
    placeholder_ar: Optional[str] = None
    placeholder_en: Optional[str] = None
    required: bool = True
    validation: Optional[dict] = None

class ClauseBlockBase(BaseModel):
    clause_id: str
    type: str  # 'header', 'parties', 'clause', 'footer'
    content_ar: str
    content_en: str
    is_mandatory: bool = False
    fields: List[ClauseFieldBase] = []
    sort_order: int
    warning_message: Optional[str] = None

class ContractStructureBase(BaseModel):
    metadata: dict
    clauses: List[ClauseBlockBase]

# Schemas للتصنيفات
class CategoryBase(BaseModel):
    name_ar: str
    name_en: str
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    legal_field: str
    business_scope: str
    complexity_level: str
    contract_type: str
    tags: List[str] = []
    icon: Optional[str] = None
    color_code: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = None

class CategoryUpdate(BaseModel):
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    legal_field: Optional[str] = None
    business_scope: Optional[str] = None
    complexity_level: Optional[str] = None
    contract_type: Optional[str] = None
    tags: Optional[List[str]] = None
    icon: Optional[str] = None
    color_code: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

class CategoryResponse(CategoryBase):
    category_id: int
    parent_id: Optional[int] = None
    template_count: int = 0
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime
    children: List['CategoryResponse'] = []
    
    class Config:
        from_attributes = True