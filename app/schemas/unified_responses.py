"""
Unified response schemas and helper functions for all API endpoints.

This module provides consistent response structures that follow the project's
.cursorrules guidelines for API responses.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse


class ErrorDetail(BaseModel):
    """Individual error detail with field and message."""
    field: Optional[str] = Field(None, description="The field that caused the error; null if general")
    message: str = Field(..., description="Explanation of the error")


def unified_response(
    success: bool, 
    message: str, 
    data: Optional[Any] = None, 
    errors: Optional[List[ErrorDetail]] = None
) -> JSONResponse:
    """
    Unified response helper for all API endpoints.
    
    Creates a consistent JSON response structure following the project's
    .cursorrules guidelines.
    
    Args:
        success: Whether the operation was successful
        message: Human-readable message describing the result
        data: Response data (dict, list, or None)
        errors: List of error details (empty list for success)
    
    Returns:
        JSONResponse with unified structure:
        {
            "success": bool,
            "message": str,
            "data": dict | list | null,
            "errors": [{"field": str | null, "message": str}]
        }
    """
    response_data = {
        "success": success,
        "message": message,
        "data": data,
        "errors": errors or []
    }
    
    return JSONResponse(content=response_data)
