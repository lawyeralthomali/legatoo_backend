"""
Routes package for API endpoints.

This package contains FastAPI routers following clean architecture principles
for proper separation of concerns and maintainability.
"""

from .auth_routes import router as auth_router
from .user_routes import router as user_router
from .profile_router import router as profile_router
from .emergency_admin_routes import router as emergency_admin_router
from .subscription_router import router as subscription_router
from .premium_router import router as premium_router

__all__ = [
    "auth_router",
    "user_router",
    "profile_router",
    "emergency_admin_router",
    "subscription_router",
    "premium_router",
]
