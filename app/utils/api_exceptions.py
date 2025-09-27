"""
Custom API exception classes for standardized error handling.

This module provides ApiException for carrying structured error payloads
that can be handled by global exception handlers.
"""

from typing import Any, Dict


class ApiException(Exception):
    """
    Custom exception for API errors that carries status code and structured payload.
    
    This exception is designed to be caught by global exception handlers
    that will return properly formatted JSON responses.
    """
    
    def __init__(self, status_code: int, payload: Dict[str, Any]):
        """
        Initialize ApiException with status code and error payload.
        
        Args:
            status_code: HTTP status code for the error
            payload: Structured error response payload
        """
        self.status_code = status_code
        self.payload = payload
        super().__init__(payload.get("message") if isinstance(payload, dict) else str(payload))
