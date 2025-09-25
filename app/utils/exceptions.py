"""
Custom exception classes for the application.

This module defines application-specific exceptions that provide
clear error context and enable proper error handling.
"""

from typing import Optional, Dict, Any


class AppException(Exception):
    """Base application exception with structured error information."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize application exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            field: Field that caused the error
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.field = field
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        field_errors: Optional[Dict[str, str]] = None
    ):
        """
        Initialize validation exception.
        
        Args:
            message: General validation message
            field: Specific field that failed validation
            field_errors: Dictionary of field-specific errors
        """
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            field=field,
            details={"field_errors": field_errors or {}}
        )


class NotFoundException(AppException):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        resource: str = "Resource",
        field: Optional[str] = None
    ):
        """
        Initialize not found exception.
        
        Args:
            resource: Name of the resource that was not found
            field: Field that caused the error
        """
        super().__init__(
            message=f"{resource} not found",
            error_code="NOT_FOUND",
            field=field
        )


class ConflictException(AppException):
    """Exception for conflict errors (e.g., duplicate resources)."""
    
    def __init__(
        self,
        message: str = "Conflict",
        field: Optional[str] = None
    ):
        """
        Initialize conflict exception.
        
        Args:
            message: Conflict message
            field: Field that caused the conflict
        """
        super().__init__(
            message=message,
            error_code="CONFLICT",
            field=field
        )


class AuthenticationException(AppException):
    """Exception for authentication errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        field: Optional[str] = None
    ):
        """
        Initialize authentication exception.
        
        Args:
            message: Authentication error message
            field: Field that caused the error
        """
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            field=field
        )


class DatabaseException(AppException):
    """Exception for database operation errors."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize database exception.
        
        Args:
            message: Database error message
            field: Field that caused the error
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            field=field,
            details=details
        )


class ExternalServiceException(AppException):
    """Exception for external service errors (e.g., Supabase)."""
    
    def __init__(
        self,
        message: str = "External service error",
        field: Optional[str] = None,
        service: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize external service exception.
        
        Args:
            message: Service error message
            field: Field that caused the error
            service: Name of the external service
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            field=field,
            details={"service": service, **(details or {})}
        )
