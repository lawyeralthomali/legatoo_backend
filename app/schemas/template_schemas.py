"""
Pydantic schemas for contract templates API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TemplateVariable(BaseModel):
    """Schema for a template variable definition."""
    name: str = Field(..., description="Variable name (e.g., 'partyA_name')")
    label: str = Field(..., description="Display label for the form field")
    type: str = Field(..., description="Field type: 'text', 'date', 'number', 'textarea'")
    required: bool = Field(default=False, description="Whether the field is required")
    default: Optional[str] = Field(None, description="Default value")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation rules")


class TemplateVariablesResponse(BaseModel):
    """Response schema for template variables endpoint."""
    id: str = Field(..., description="Template ID")
    title: str = Field(..., description="Template title")
    description: Optional[str] = Field(None, description="Template description")
    variables: List[TemplateVariable] = Field(..., description="List of form variables")


class GenerateContractRequest(BaseModel):
    """Request schema for contract generation."""
    filled_data: Dict[str, Any] = Field(..., description="User-provided form data")


class GenerateContractResponse(BaseModel):
    """Response schema for contract generation."""
    contract_id: str = Field(..., description="Generated contract ID")
    pdf_url: str = Field(..., description="URL to download/view the generated PDF")
    success: bool = Field(default=True, description="Operation success status")

