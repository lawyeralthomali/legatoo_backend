"""
Services package for business logic layer.

This package contains service implementations following SOLID principles
for clean separation of concerns and business logic encapsulation.

NEW STRUCTURE (October 2025):
- auth/: Authentication and email services
- legal/: All legal-related services
  - knowledge/: Legal knowledge management (laws, cases, hierarchy)
  - processing/: Document processing and chunking
  - search/: Search and embedding services
  - analysis/: Legal analysis and RAG
  - ingestion/: Data ingestion pipelines
- user_management/: User and profile management
- subscription/: Subscription and billing
- contracts/: Contract management
- shared/: Shared/deprecated services
"""

# Auth Services
from .auth.auth_service import AuthService
from .auth.email_service import EmailService

# Legal Services
from .legal.knowledge import (
    LegalKnowledgeService,
    LegalLawsService,
    LegalHierarchyService,
    LegalCaseService,
)
from .legal.processing import (
    ChunkProcessingService,
    DocumentProcessingService,
    SemanticChunkingService,
    ArabicLegalDocumentProcessor,
)
from .legal.search import (
    ArabicLegalSearchService,
    ArabicLegalEmbeddingService,
)
from .legal.analysis import (
    GeminiLegalAnalyzer,
    HybridAnalysisService,
    LegalRAGService,
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

# Contract Services
from .contracts import (
    ContractCategoryService,
    ContractTemplateService,
    UserContractService,
    UserFavoriteService,
)

# Shared/Deprecated Services (for backward compatibility)
from .shared import (
    EmbeddingService,
    RAGService,
    SemanticSearchService,
)

__all__ = [
    # Auth
    "AuthService",
    "EmailService",
    
    # Legal - Knowledge
    "LegalKnowledgeService",
    "LegalLawsService",
    "LegalHierarchyService",
    "LegalCaseService",
    
    # Legal - Processing
    "ChunkProcessingService",
    "DocumentProcessingService",
    "SemanticChunkingService",
    "ArabicLegalDocumentProcessor",
    
    # Legal - Search (⭐ RECOMMENDED)
    "ArabicLegalSearchService",
    "ArabicLegalEmbeddingService",
    
    # Legal - Analysis
    "GeminiLegalAnalyzer",
    "HybridAnalysisService",
    "LegalRAGService",
    
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
    
    # Contracts
    "ContractCategoryService",
    "ContractTemplateService",
    "UserContractService",
    "UserFavoriteService",
    
    # Shared (deprecated - use Arabic services instead)
    "EmbeddingService",
    "RAGService",
    "SemanticSearchService",
]
