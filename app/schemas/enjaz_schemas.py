"""
Enjaz-related schemas for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class EnjazCredentialsRequest(BaseModel):
    """Schema for Enjaz credentials connection request."""
    username: str = Field(..., min_length=1, description="Enjaz username")
    password: str = Field(..., min_length=1, description="Enjaz password")


class EnjazAccountResponse(BaseModel):
    """Schema for Enjaz account response (without sensitive data)."""
    id: int
    username: str = Field(..., description="Encrypted username (masked)")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CaseData(BaseModel):
    """Schema for individual case data from Enjaz."""
    case_number: str = Field(..., description="Case number")
    case_type: str = Field(..., description="Type of case")
    status: str = Field(..., description="Current case status")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional case information")


class CaseImportedResponse(BaseModel):
    """Schema for imported case response."""
    id: int
    case_number: str
    case_type: str
    status: str
    case_data: Optional[str] = None  # JSON string
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SyncCasesResponse(BaseModel):
    """Schema for sync cases operation response."""
    success: bool
    message: str
    cases_imported: int
    cases_updated: int
    total_cases: int


class CasesListResponse(BaseModel):
    """Schema for cases list response."""
    success: bool
    message: str
    data: List[CaseImportedResponse]
    total_count: int
