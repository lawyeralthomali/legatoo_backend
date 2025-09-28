"""
Enhanced logging configuration with correlation IDs and security features.

This module provides enterprise-grade logging with request tracing,
sensitive data masking, and structured logging for production environments.
"""

import logging
import logging.config
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import json
import re


class CorrelationFilter(logging.Filter):
    """Logging filter to add correlation ID to log records."""
    
    def filter(self, record):
        # Add correlation ID if not present
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(self, 'correlation_id', 'no-correlation-id')
        return True


class SecurityFilter(logging.Filter):
    """Logging filter to mask sensitive data."""
    
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', r'password="***"'),
        (r'token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', r'token="***"'),
        (r'email["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', r'email="***@***.***"'),
        (r'authorization["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', r'authorization="***"'),
    ]
    
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Mask sensitive data in log messages
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg, flags=re.IGNORECASE)
        
        return True


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for production logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', 'no-correlation-id'),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info', 'correlation_id']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


def setup_logging(correlation_id: Optional[str] = None) -> logging.Logger:
    """
    Setup enhanced logging configuration.
    
    Args:
        correlation_id: Optional correlation ID for request tracing
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Generate correlation ID if not provided
    if not correlation_id:
        correlation_id = str(uuid.uuid4())[:8]
    
    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                '()': StructuredFormatter,
            }
        },
        'filters': {
            'correlation': {
                '()': CorrelationFilter,
            },
            'security': {
                '()': SecurityFilter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filters': ['correlation', 'security'],
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'json',
                'filters': ['correlation', 'security'],
                'filename': 'logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filters': ['correlation', 'security'],
                'filename': 'logs/errors.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            'app': {
                'level': 'DEBUG',
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'app.services': {
                'level': 'DEBUG',
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'app.routes': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': ['file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        }
    }
    
    logging.config.dictConfig(logging_config)
    
    # Set correlation ID for the current context
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'filters'):
            for filter_obj in handler.filters:
                if isinstance(filter_obj, CorrelationFilter):
                    filter_obj.correlation_id = correlation_id
    
    return logging.getLogger('app')


def get_logger(name: str, correlation_id: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with correlation ID.
    
    Args:
        name: Logger name (usually __name__)
        correlation_id: Optional correlation ID
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Set correlation ID if provided
    if correlation_id:
        for handler in logger.handlers:
            if hasattr(handler, 'filters'):
                for filter_obj in handler.filters:
                    if isinstance(filter_obj, CorrelationFilter):
                        filter_obj.correlation_id = correlation_id
    
    return logger


def mask_email(email: str) -> str:
    """Mask email address for logging."""
    if not email or '@' not in email:
        return '***@***.***'
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    domain_parts = domain.split('.')
    if len(domain_parts) >= 2:
        masked_domain = '*' * len(domain_parts[0]) + '.' + '.'.join(domain_parts[1:])
    else:
        masked_domain = '*' * len(domain)
    
    return f"{masked_local}@{masked_domain}"


def log_auth_attempt(logger: logging.Logger, email: str, success: bool, 
                    correlation_id: Optional[str] = None, **kwargs):
    """Log authentication attempt with security considerations."""
    masked_email = mask_email(email)
    
    log_data = {
        'correlation_id': correlation_id,
        'email': masked_email,
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
        **kwargs
    }
    
    if success:
        logger.info(f"Authentication successful for {masked_email}", extra=log_data)
    else:
        logger.warning(f"Authentication failed for {masked_email}", extra=log_data)


def log_security_event(logger: logging.Logger, event_type: str, 
                      correlation_id: Optional[str] = None, **kwargs):
    """Log security-related events."""
    log_data = {
        'correlation_id': correlation_id,
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        **kwargs
    }
    
    logger.warning(f"Security event: {event_type}", extra=log_data)
