"""
Pydantic schemas for Contracts Library API.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============ Contract Schemas ============

class ContractBase(BaseModel):
    """Base contract schema."""
    title: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    language: str = Field("en", max_length=10)
    status: str = Field("draft", pattern="^(draft|active|archived)$")
    content: Optional[str] = None


class ContractCreate(ContractBase):
    """Schema for creating a new contract."""
    pass


class ContractUpdate(BaseModel):
    """Schema for updating a contract."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    status: Optional[str] = Field(None, pattern="^(draft|active|archived)$")
    content: Optional[str] = None


class ContractResponse(ContractBase):
    """Schema for contract response."""
    id: str
    version: int
    ai_generated: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    """Schema for contract list response."""
    contracts: List[ContractResponse]
    total: int
    page: int
    page_size: int


# ============ Template Schemas ============

class TemplateBase(BaseModel):
    """Base template schema."""
    name: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    content: str = Field(..., min_length=1)
    language: str = Field("en", max_length=10)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    is_public: bool = False


class TemplateCreate(TemplateBase):
    """Schema for creating a new template."""
    pass


class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    content: Optional[str] = Field(None, min_length=1)
    language: Optional[str] = Field(None, max_length=10)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    is_public: Optional[bool] = None


class TemplateResponse(TemplateBase):
    """Schema for template response."""
    id: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============ Revision Schemas ============

class RevisionResponse(BaseModel):
    """Schema for revision response."""
    id: str
    contract_id: str
    revision_number: int
    changes_summary: Optional[str]
    updated_content: str
    updated_by: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RevisionCreate(BaseModel):
    """Schema for creating a revision."""
    changes_summary: Optional[str] = None
    updated_content: str = Field(..., min_length=1)


class RevisionHistoryResponse(BaseModel):
    """Schema for revision history response."""
    contract_id: str
    revisions: List[RevisionResponse]
    total_revisions: int


# ============ AI Generation Schemas ============

class AIGenerateRequest(BaseModel):
    """Schema for AI contract generation request."""
    prompt_text: str = Field(..., min_length=10, description="Natural language description of the contract")
    category: Optional[str] = Field(None, description="Contract category")
    jurisdiction: Optional[str] = Field(None, description="Legal jurisdiction")
    language: Optional[str] = Field("en", description="Contract language")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Structured data for placeholders (e.g., party names, dates)")
    ai_model: Optional[str] = Field("gemini-2.0-flash-exp", description="AI model to use")


class AIGenerateResponse(BaseModel):
    """Schema for AI generation response."""
    request_id: str
    generated_content: str
    ai_model: str
    created_at: datetime
    contract_id: Optional[str] = None  # If user saved it as a contract


class AIRequestResponse(BaseModel):
    """Schema for AI request history response."""
    id: str
    prompt_text: str
    ai_model: str
    generated_content: Optional[str]
    created_at: datetime
    used_in_contract_id: Optional[str]
    
    class Config:
        from_attributes = True


# ============ Search & Filter Schemas ============

class ContractFilters(BaseModel):
    """Schema for contract search filters."""
    category: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: Optional[str] = None
    language: Optional[str] = None
    ai_generated: Optional[bool] = None
    search_query: Optional[str] = None  # Full-text search
    created_by: Optional[int] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class TemplateFilters(BaseModel):
    """Schema for template search filters."""
    category: Optional[str] = None
    jurisdiction: Optional[str] = None
    language: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None
    search_query: Optional[str] = None
    created_by: Optional[int] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
