"""
Schemas package for request/response validation.

This package contains Pydantic models for API request/response validation
following clean architecture principles.
"""

from .category import (
    ClauseFieldBase, ClauseBlockBase, ContractStructureBase,
    CategoryBase, CategoryCreate, CategoryUpdate, CategoryResponse
)
from .template import (
    TemplateBase, TemplateCreate, TemplateUpdate, TemplateResponse
)
from .user_contract import (
    UserContractBase, UserContractCreate, UserContractUpdate, UserContractResponse,
    ContractGenerationRequest, ContractGenerationResponse, ContractStatusUpdate,
    UserContractSummary
)
from .favorite import (
    FavoriteBase, FavoriteCreate, FavoriteResponse, FavoriteToggleResponse,
    FavoriteCountResponse, MostFavoritedTemplate
)
from .response import ApiResponse, ErrorResponse

__all__ = [
    # Category schemas
    "ClauseFieldBase", "ClauseBlockBase", "ContractStructureBase",
    "CategoryBase", "CategoryCreate", "CategoryUpdate", "CategoryResponse",
    
    # Template schemas
    "TemplateBase", "TemplateCreate", "TemplateUpdate", "TemplateResponse",
    
    # User Contract schemas
    "UserContractBase", "UserContractCreate", "UserContractUpdate", "UserContractResponse",
    "ContractGenerationRequest", "ContractGenerationResponse", "ContractStatusUpdate",
    "UserContractSummary",
    
    # Favorite schemas
    "FavoriteBase", "FavoriteCreate", "FavoriteResponse", "FavoriteToggleResponse",
    "FavoriteCountResponse", "MostFavoritedTemplate",
    
    # Response schemas
    "ApiResponse", "ErrorResponse"
]
