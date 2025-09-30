from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from .template import TemplateResponse


class UserContractBase(BaseModel):
    template_id: int
    contract_data: Dict[str, Any]
    status: str = "draft"


class UserContractCreate(UserContractBase):
    pass


class UserContractUpdate(BaseModel):
    contract_data: Optional[Dict[str, Any]] = None
    final_content: Optional[str] = None
    status: Optional[str] = None


class UserContractResponse(UserContractBase):
    user_contract_id: int
    user_id: int
    final_content: str
    created_at: datetime
    updated_at: Optional[datetime]
    template: Optional[TemplateResponse] = None
    
    class Config:
        from_attributes = True


class ContractGenerationRequest(BaseModel):
    template_id: int
    contract_data: Dict[str, Any]


class ContractGenerationResponse(BaseModel):
    user_contract_id: int
    final_content: str
    status: str
    template_title: str


class ContractStatusUpdate(BaseModel):
    status: str  # 'draft', 'completed', 'signed'


class UserContractSummary(BaseModel):
    total_contracts: int
    by_status: Dict[str, int]
    draft_count: int
    completed_count: int
    signed_count: int
