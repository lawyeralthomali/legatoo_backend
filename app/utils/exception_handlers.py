"""
Centralized exception handlers for the FastAPI application.

This module provides global exception handlers that transform all exceptions
into the unified ApiResponse format, ensuring consistent error responses.
"""

import logging
from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError

from ..schemas.response import (
    ApiResponse, ErrorResponse, ErrorDetail,
    create_error_response, create_validation_error_response,
    create_not_found_response, create_conflict_response
)
from .exceptions import (
    AppException, ValidationException, NotFoundException,
    ConflictException, AuthenticationException, DatabaseException,
    ExternalServiceException
)

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions.
    
    Args:
        request: FastAPI request object
        exc: Application exception
        
    Returns:
        JSONResponse with unified error format
    """
    logger.warning(f"Application exception: {exc.message}", extra={
        "error_code": exc.error_code,
        "field": exc.field,
        "details": exc.details
    })
    
    response = ErrorResponse(
        message=exc.message,
        errors=[ErrorDetail(field=exc.field, message=exc.message)],
        data=None
    )
    
    return JSONResponse(
        status_code=400,
        content=response.dict()
    )


async def validation_exception_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """
    Handle validation exceptions with field-specific errors.
    
    Args:
        request: FastAPI request object
        exc: Validation exception
        
    Returns:
        JSONResponse with validation errors
    """
    logger.warning(f"Validation exception: {exc.message}", extra={
        "field": exc.field,
        "field_errors": exc.details.get("field_errors", {})
    })
    
    errors = []
    field_errors = exc.details.get("field_errors", {})
    
    if field_errors:
        for field, error_msg in field_errors.items():
            errors.append(ErrorDetail(field=field, message=error_msg))
    else:
        errors.append(ErrorDetail(field=exc.field, message=exc.message))
    
    response = ErrorResponse(
        message=exc.message,
        errors=errors,
        data=None
    )
    
    return JSONResponse(
        status_code=422,
        content=response.dict()
    )


async def not_found_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    """
    Handle not found exceptions.
    
    Args:
        request: FastAPI request object
        exc: Not found exception
        
    Returns:
        JSONResponse with not found error
    """
    logger.info(f"Resource not found: {exc.message}")
    
    response = create_not_found_response(
        resource=exc.message.replace(" not found", ""),
        field=exc.field
    )
    
    return JSONResponse(
        status_code=404,
        content=response.dict()
    )


async def conflict_exception_handler(request: Request, exc: ConflictException) -> JSONResponse:
    """
    Handle conflict exceptions.
    
    Args:
        request: FastAPI request object
        exc: Conflict exception
        
    Returns:
        JSONResponse with conflict error
    """
    logger.warning(f"Conflict exception: {exc.message}")
    
    response = create_conflict_response(
        message=exc.message,
        field=exc.field
    )
    
    return JSONResponse(
        status_code=409,
        content=response.dict()
    )


async def authentication_exception_handler(request: Request, exc: AuthenticationException) -> JSONResponse:
    """
    Handle authentication exceptions.
    
    Args:
        request: FastAPI request object
        exc: Authentication exception
        
    Returns:
        JSONResponse with authentication error
    """
    logger.warning(f"Authentication exception: {exc.message}")
    
    response = ErrorResponse(
        message=exc.message,
        errors=[ErrorDetail(field=exc.field, message=exc.message)],
        data=None
    )
    
    return JSONResponse(
        status_code=401,
        content=response.dict()
    )


async def database_exception_handler(request: Request, exc: DatabaseException) -> JSONResponse:
    """
    Handle database exceptions.
    
    Args:
        request: FastAPI request object
        exc: Database exception
        
    Returns:
        JSONResponse with database error
    """
    logger.error(f"Database exception: {exc.message}", extra={
        "field": exc.field,
        "details": exc.details
    })
    
    response = ErrorResponse(
        message="Database operation failed",
        errors=[ErrorDetail(field=exc.field, message="An internal error occurred")],
        data=None
    )
    
    return JSONResponse(
        status_code=500,
        content=response.dict()
    )


async def external_service_exception_handler(request: Request, exc: ExternalServiceException) -> JSONResponse:
    """
    Handle external service exceptions.
    
    Args:
        request: FastAPI request object
        exc: External service exception
        
    Returns:
        JSONResponse with external service error
    """
    logger.error(f"External service exception: {exc.message}", extra={
        "service": exc.details.get("service"),
        "field": exc.field,
        "details": exc.details
    })
    
    response = ErrorResponse(
        message=exc.message,
        errors=[ErrorDetail(field=exc.field, message=exc.message)],
        data=None
    )
    
    return JSONResponse(
        status_code=502,
        content=response.dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with HTTP error
    """
    logger.warning(f"HTTP exception: {exc.detail}")
    
    response = ErrorResponse(
        message=str(exc.detail),
        errors=[ErrorDetail(message=str(exc.detail))],
        data=None
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.dict()
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: Validation error
        
    Returns:
        JSONResponse with validation errors
    """
    logger.warning(f"Validation error: {exc.errors()}")
    
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"]) if error["loc"] else None
        message = error["msg"]
        errors.append(ErrorDetail(field=field, message=message))
    
    response = ErrorResponse(
        message="Validation failed",
        errors=errors,
        data=None
    )
    
    return JSONResponse(
        status_code=422,
        content=response.dict()
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Handle SQLAlchemy integrity errors.
    
    Args:
        request: FastAPI request object
        exc: Integrity error
        
    Returns:
        JSONResponse with integrity error
    """
    logger.warning(f"Integrity error: {str(exc)}")
    
    # Check for common integrity constraint violations
    error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
        response = create_conflict_response(
            message="Resource already exists",
            field=None
        )
        status_code = 409
    elif "foreign key" in error_msg.lower():
        response = ErrorResponse(
            message="Referenced resource not found",
            errors=[ErrorDetail(message="The referenced resource does not exist")],
            data=None
        )
        status_code = 400
    else:
        response = ErrorResponse(
            message="Database constraint violation",
            errors=[ErrorDetail(message="The operation violates database constraints")],
            data=None
        )
        status_code = 400
    
    return JSONResponse(
        status_code=status_code,
        content=response.dict()
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle general SQLAlchemy errors.
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy error
        
    Returns:
        JSONResponse with database error
    """
    logger.error(f"SQLAlchemy error: {str(exc)}")
    
    response = ErrorResponse(
        message="Database operation failed",
        errors=[ErrorDetail(message="An internal database error occurred")],
        data=None
    )
    
    return JSONResponse(
        status_code=500,
        content=response.dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions not caught by specific handlers.
    
    Args:
        request: FastAPI request object
        exc: General exception
        
    Returns:
        JSONResponse with generic error
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    response = ErrorResponse(
        message="Internal server error",
        errors=[ErrorDetail(message="An unexpected error occurred")],
        data=None
    )
    
    return JSONResponse(
        status_code=500,
        content=response.dict()
    )
