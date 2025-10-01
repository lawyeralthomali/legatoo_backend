"""
Repository package for data access layer.

This package contains repository implementations following the Repository pattern
for clean separation of concerns and testability.
"""

from .base import BaseRepository
from .enjaz_repository import EnjazRepository
from .profile_repository import ProfileRepository
from .user_repository import UserRepository
from .contract_category_repository import ContractCategoryRepository
from .contract_template_repository import ContractTemplateRepository
from .user_contract_repository import UserContractRepository
from .user_favorite_repository import UserFavoriteRepository
from .legal_document_repository import LegalDocumentRepository
from .refresh_token_repository import RefreshTokenRepository

__all__ = [
    "BaseRepository",
    "EnjazRepository", 
    "ProfileRepository",
    "UserRepository",
    "ContractCategoryRepository",
    "ContractTemplateRepository",
    "UserContractRepository",
    "UserFavoriteRepository",
    "LegalDocumentRepository",
    "RefreshTokenRepository"
]