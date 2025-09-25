"""
Unified response schemas for all API endpoints.

This module provides consistent response structures that follow the project's
.cursorrules guidelines for API responses.
"""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Individual error detail with field and message."""
    field: Optional[str] = Field(None, description="The field that caused the error; null if general")
    message: str = Field(..., description="Explanation of the error")


class UnifiedResponse(BaseModel):
    """
    Base unified response structure for all API endpoints.
    
    Follows the project's .cursorrules guidelines:
    - success: bool - true if request succeeded, false if error
    - message: str - human-readable message describing the result
    - data: dict | list | null - payload for success, null for errors
    - errors: list - list of field-specific error objects; empty list if none
    """
    success: bool = Field(..., description="True if the request succeeded, false if there was an error")
    message: str = Field(..., description="Human-readable message describing the result")
    data: Optional[Union[Dict[str, Any], List[Any]]] = Field(None, description="Payload for success, null for errors")
    errors: List[ErrorDetail] = Field(default_factory=list, description="List of field-specific error objects; empty list if none")


class SuccessResponse(UnifiedResponse):
    """Response for successful operations."""
    success: bool = Field(True, description="Always true for success responses")
    data: Union[Dict[str, Any], List[Any]] = Field(..., description="Success payload data")
    errors: List[ErrorDetail] = Field(default_factory=list, description="Empty list for success responses")


class ErrorResponse(UnifiedResponse):
    """Response for error operations."""
    success: bool = Field(False, description="Always false for error responses")
    data: Optional[Union[Dict[str, Any], List[Any]]] = Field(None, description="Always null for error responses")
    errors: List[ErrorDetail] = Field(..., description="List of error details")


class ValidationErrorResponse(ErrorResponse):
    """Response for validation errors."""
    message: str = Field(default="Validation failed", description="Default message for validation errors")


class AuthenticationErrorResponse(ErrorResponse):
    """Response for authentication errors."""
    message: str = Field(default="Authentication failed", description="Default message for authentication errors")


class NotFoundErrorResponse(ErrorResponse):
    """Response for not found errors."""
    message: str = Field(default="Resource not found", description="Default message for not found errors")


class ConflictErrorResponse(ErrorResponse):
    """Response for conflict errors (e.g., duplicate resources)."""
    message: str = Field(default="Resource conflict", description="Default message for conflict errors")


class InternalErrorResponse(ErrorResponse):
    """Response for internal server errors."""
    message: str = Field(default="Internal server error", description="Default message for internal errors")


# Helper functions for creating responses
def create_success_response(
    message: str,
    data: Union[Dict[str, Any], List[Any]],
    errors: Optional[List[ErrorDetail]] = None
) -> SuccessResponse:
    """Create a success response."""
    return SuccessResponse(
        success=True,
        message=message,
        data=data,
        errors=errors or []
    )


def create_error_response(
    message: str,
    errors: List[ErrorDetail],
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
) -> ErrorResponse:
    """Create an error response."""
    return ErrorResponse(
        success=False,
        message=message,
        data=data,
        errors=errors
    )


def create_validation_error_response(
    errors: List[ErrorDetail],
    message: str = "Validation failed"
) -> ValidationErrorResponse:
    """Create a validation error response."""
    return ValidationErrorResponse(
        success=False,
        message=message,
        data=None,
        errors=errors
    )


def create_authentication_error_response(
    message: str = "Authentication failed",
    field: Optional[str] = None
) -> AuthenticationErrorResponse:
    """Create an authentication error response."""
    return AuthenticationErrorResponse(
        success=False,
        message=message,
        data=None,
        errors=[ErrorDetail(field=field, message=message)]
    )


def create_not_found_error_response(
    message: str = "Resource not found",
    field: Optional[str] = None
) -> NotFoundErrorResponse:
    """Create a not found error response."""
    return NotFoundErrorResponse(
        success=False,
        message=message,
        data=None,
        errors=[ErrorDetail(field=field, message=message)]
    )


def create_conflict_error_response(
    message: str = "Resource conflict",
    field: Optional[str] = None
) -> ConflictErrorResponse:
    """Create a conflict error response."""
    return ConflictErrorResponse(
        success=False,
        message=message,
        data=None,
        errors=[ErrorDetail(field=field, message=message)]
    )


def create_internal_error_response(
    message: str = "Internal server error",
    field: Optional[str] = None
) -> InternalErrorResponse:
    """Create an internal error response."""
    return InternalErrorResponse(
        success=False,
        message=message,
        data=None,
        errors=[ErrorDetail(field=field, message=message)]
    )
