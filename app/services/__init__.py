"""
Services package for business logic layer.

This package contains service implementations following SOLID principles
for clean separation of concerns and business logic encapsulation.

NEW STRUCTURE (October 2025):
- auth/: Authentication and email services
- legal/: All legal-related services
  - knowledge/: Legal knowledge management (laws, cases, hierarchy)
  - ingestion/: Data ingestion pipelines
- user_management/: User and profile management
- subscription/: Subscription and billing
"""

# Auth Services
from .auth.auth_service import AuthService
from .auth.email_service import EmailService

# Legal Services
from .legal.knowledge import (
    LegalLawsService,
    LegalCaseService,
)
from .legal.ingestion import (
    LegalCaseIngestionService,
)

# User Management Services
from .user_management import (
    UserService,
    ProfileService,
    SuperAdminService,
)

# Subscription Services
from .subscription import (
    PlanService,
    SubscriptionService,
    PremiumService,
)


# Shared/Deprecated Services (for backward compatibility)
# from .shared import (
#     SemanticSearchService,
# )

__all__ = [
    # Auth
    "AuthService",
    "EmailService",
    
    # Legal - Knowledge
    "LegalLawsService",
    "LegalCaseService",
    
    
    
    
    # Legal - Ingestion
    "LegalCaseIngestionService",
    
    # User Management
    "UserService",
    "ProfileService",
    "SuperAdminService",
    
    # Subscription
    "PlanService",
    "SubscriptionService",
    "PremiumService",
    
    
    # Shared (deprecated - use Arabic services instead)
    # "SemanticSearchService",
]
