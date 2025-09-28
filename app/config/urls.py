"""
Centralized URL configuration for the application.

This module provides a single source of truth for all URLs used across
the application, including frontend URLs, API endpoints, and redirect URLs.
"""

import os
from typing import Dict, Any


class URLConfig:
    """
    Centralized URL configuration class.
    
    All URLs are managed from this single point to ensure consistency
    across the application and easy maintenance.
    """
    
    def __init__(self):
        # Environment-based configuration
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Base URLs
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
        self.api_base_url = f"{self.backend_url}/api/v1"
        
        # Production URLs (override for production)
        if self.environment == "production":
            self.frontend_url = os.getenv("FRONTEND_URL", "https://legatoo.westlinktowing.com")
            self.backend_url = os.getenv("BACKEND_URL", "https://api.legatoo.westlinktowing.com")
            self.api_base_url = f"{self.backend_url}/api/v1"
    
    @property
    def auth_urls(self) -> Dict[str, str]:
        """Authentication-related URLs."""
        return {
            "login": f"{self.frontend_url}/auth/login",
            "signup": f"{self.frontend_url}/auth/signup",
            "forgot_password": f"{self.frontend_url}/auth/forgot-password",
            "email_verification": f"{self.frontend_url}/email-verification.html",
            "password_reset": f"{self.frontend_url}/password-reset.html",
            "dashboard": f"{self.frontend_url}/dashboard",
        }
    
    @property
    def api_urls(self) -> Dict[str, str]:
        """API endpoint URLs."""
        return {
            "auth_base": f"{self.api_base_url}/auth",
            "login": f"{self.api_base_url}/auth/login",
            "signup": f"{self.api_base_url}/auth/signup",
            "verify_email": f"{self.api_base_url}/auth/verify-email",
            "forgot_password": f"{self.api_base_url}/auth/forgot-password",
            "confirm_password_reset": f"{self.api_base_url}/auth/confirm-password-reset",
            "refresh_token": f"{self.api_base_url}/auth/refresh-token",
            "logout": f"{self.api_base_url}/auth/logout",
            "profile": f"{self.api_base_url}/profiles/me",
            "subscriptions": f"{self.api_base_url}/subscriptions/status",
            "plans": f"{self.api_base_url}/subscriptions/plans",
            "premium": f"{self.api_base_url}/premium/status",
            "features": f"{self.api_base_url}/premium/feature-limits",
        }
    
    @property
    def email_urls(self) -> Dict[str, str]:
        """Email template URLs."""
        return {
            "verification": f"{self.frontend_url}/email-verification.html",
            "password_reset": f"{self.frontend_url}/password-reset.html",
        }
    
    def get_verification_url(self, token: str) -> str:
        """Get email verification URL with token."""
        return f"{self.email_urls['verification']}?token={token}"
    
    def get_password_reset_url(self, token: str) -> str:
        """Get password reset URL with token."""
        return f"{self.email_urls['password_reset']}?token={token}"
    
    def get_api_url(self, endpoint: str) -> str:
        """Get API URL for specific endpoint."""
        return self.api_urls.get(endpoint, f"{self.api_base_url}/{endpoint}")
    
    def get_frontend_url(self, path: str = "") -> str:
        """Get frontend URL with optional path."""
        return f"{self.frontend_url}/{path.lstrip('/')}" if path else self.frontend_url
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for JavaScript usage."""
        return {
            "environment": self.environment,
            "frontend_url": self.frontend_url,
            "backend_url": self.backend_url,
            "api_base_url": self.api_base_url,
            "auth_urls": self.auth_urls,
            "api_urls": self.api_urls,
            "email_urls": self.email_urls,
        }


# Global instance
url_config = URLConfig()


def get_url_config() -> URLConfig:
    """Get the global URL configuration instance."""
    return url_config
