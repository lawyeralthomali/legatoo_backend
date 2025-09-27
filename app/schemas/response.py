"""
Unified API response schemas for consistent API responses across the application.

This module defines the standard response format that all endpoints must follow,
ensuring consistency and predictability for API consumers.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi import HTTPException


class ErrorDetail(BaseModel):
    """Individual error detail with field and message information."""
    field: Optional[str] = Field(None, description="The field that caused the error; null if general")
    message: str = Field(..., description="Explanation of the error")


class ApiResponse(BaseModel):
    """Unified API response model for all endpoints."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message describing the result")
    data: Optional[Any] = Field(None, description="Response data (dict, list, or null)")
    errors: Optional[List[ErrorDetail]] = Field(None, description="List of error details")


class SuccessResponse(ApiResponse):
    """Success response model with success=True."""
    success: bool = True
    errors: Optional[List[ErrorDetail]] = Field(default_factory=list)


class ErrorResponse(ApiResponse):
    """Error response model with success=False."""
    success: bool = False
    data: Optional[Any] = None


def create_success_response(
    message: str = "Operation successful",
    data: Optional[Any] = None
) -> SuccessResponse:
    """
    Create a standardized success response.
    
    Args:
        message: Success message
        data: Response data
        
    Returns:
        SuccessResponse instance
    """
    return SuccessResponse(message=message, data=data)


def create_error_response(
    message: str = "Operation failed",
    errors: Optional[List[ErrorDetail]] = None,
    data: Optional[Any] = None
) -> ErrorResponse:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        errors: List of error details
        data: Response data (usually None for errors)
        
    Returns:
        ErrorResponse instance
    """
    if errors is None:
        errors = [ErrorDetail(message=message)]
    
    return ErrorResponse(message=message, errors=errors, data=data)


def create_validation_error_response(
    message: str = "Validation failed",
    field_errors: Dict[str, str] = None
) -> ErrorResponse:
    """
    Create a validation error response with field-specific errors.
    
    Args:
        message: General validation message
        field_errors: Dictionary mapping field names to error messages
        
    Returns:
        ErrorResponse instance with field-specific errors
    """
    errors = []
    if field_errors:
        for field, error_msg in field_errors.items():
            errors.append(ErrorDetail(field=field, message=error_msg))
    else:
        errors.append(ErrorDetail(message=message))
    
    return ErrorResponse(message=message, errors=errors)


def create_not_found_response(
    resource: str = "Resource",
    field: Optional[str] = None
) -> ErrorResponse:
    """
    Create a not found error response.
    
    Args:
        resource: Name of the resource that was not found
        field: Field that caused the error
        
    Returns:
        ErrorResponse instance
    """
    return ErrorResponse(
        message=f"{resource} not found",
        errors=[ErrorDetail(field=field, message=f"The requested {resource.lower()} was not found")]
    )


def create_conflict_response(
    message: str = "Conflict",
    field: Optional[str] = None
) -> ErrorResponse:
    """
    Create a conflict error response.
    
    Args:
        message: Conflict message
        field: Field that caused the conflict
        
    Returns:
        ErrorResponse instance
    """
    return ErrorResponse(
        message=message,
        errors=[ErrorDetail(field=field, message=message)]
    )

def raise_error_response(
    status_code: int,
    message: str,
    field: Optional[str] = None,
    errors: Optional[List[ErrorDetail]] = None
) -> None:
    """
    Raise ApiException carrying a standardized error payload.
    Callers expect this function to raise (no return).
    """
    from ..utils.api_exceptions import ApiException
    
    # Build normalized error list
    if errors is None:
        errors_payload = [{"field": field, "message": message}]
    else:
        # Convert ErrorDetail models to dicts if necessary
        errors_payload = [
            (e.model_dump() if hasattr(e, "model_dump") else {"field": getattr(e, "field", None), "message": getattr(e, "message", str(e))})
            for e in errors
        ]

    payload = {
        "success": False,
        "message": message,
        "data": None,
        "errors": errors_payload
    }

    # Raise the custom ApiException with full payload (handler will serialize it)
    raise ApiException(status_code=status_code, payload=payload)