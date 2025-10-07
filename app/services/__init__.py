"""
Services package for business logic layer.

This package contains service implementations following SOLID principles
for clean separation of concerns and business logic encapsulation.
"""

from .auth_service import AuthService
from .email_service import EmailService
from .legal_assistant_service import LegalAssistantService
from .document_processing_service import DocumentProcessingService
from .embedding_service import EmbeddingService
from .semantic_search_service import SemanticSearchService
from .plan_service import PlanService
from .premium_service import PremiumService
from .profile_service import ProfileService
from .subscription_service import SubscriptionService
from .super_admin_service import SuperAdminService
from .user_service import UserService
from .contract_category_service import ContractCategoryService
from .contract_template_service import ContractTemplateService
from .user_contract_service import UserContractService
from .user_favorite_service import UserFavoriteService

__all__ = [
    "AuthService",
    "EmailService",
    "LegalAssistantService",
    "DocumentProcessingService",
    "EmbeddingService",
    "SemanticSearchService",
    "PlanService",
    "PremiumService",
    "ProfileService",
    "SubscriptionService",
    "SuperAdminService",
    "UserService",
    "ContractCategoryService",
    "ContractTemplateService",
    "UserContractService",
    "UserFavoriteService"
]
